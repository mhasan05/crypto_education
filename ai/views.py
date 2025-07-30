from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status,permissions, parsers
from .models import *
import uuid
from .serializers import *
from .utils import *
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import NotFound, APIException
from rest_framework.permissions import IsAuthenticated
import random
import string
import uuid
import google.generativeai as genai
import re
from django.db.models import Count
from datetime import datetime, timedelta

@method_decorator(csrf_exempt, name='dispatch')
class PrintCollections(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        videos = Video.objects.all()
        subtitles = Subtitle.objects.all()

        video_data = VideoSerializer(videos, many=True).data
        subtitle_data = SubtitleSerializer(subtitles, many=True).data

        return Response({
            "videos": video_data,
            "subtitles": subtitle_data
        })

@method_decorator(csrf_exempt, name='dispatch')
class CreateVideoChatSession(APIView):

    def post(self, request):
        session_id = generate_session_id()
        return Response({
            "session_id": session_id,
            "message": "Session created successfully"
        })

@method_decorator(csrf_exempt, name='dispatch')
class AskQuestionFromVideo(APIView):
    def post(self, request, object_id):
        object_id = str(object_id).strip()
        try:
            question = request.data.get("question", "").strip().lower()
            session_id = request.data.get("session_id", "").strip()
            language = request.query_params.get("language", "en").lower()

            if not question:
                return Response({"detail": "Question cannot be empty."}, status=400)
            if not session_id:
                return Response({"detail": "Session ID is required."}, status=400)

            greetings = [
                "hi", "hello", "hey", "greetings", "good morning", "good evening", "good afternoon",
                "hallo", "guten morgen", "guten abend", "guten tag", "servus", "moin", "grüß dich"
            ]

            if any(re.fullmatch(rf"{greet}[!., ]*", question) for greet in greetings):
                welcome_en = (
                    "👋 Hello! I’m your Crypto Education Assistant. "
                    "You can ask me anything from this video."
                )
                welcome_de = (
                    "👋 Hallo! Ich bin dein Krypto-Bildungsassistent. "
                    "Du kannst mich alles zu diesem Video fragen."
                )
                welcome_message = welcome_de if language == "german" else welcome_en

                store_chat_message_in_chroma("user", question, session_id, object_id)
                store_chat_message_in_chroma("assistant", welcome_message, session_id, object_id)

                return Response({"answer": welcome_message})

            query_embedding = embeddings_model.embed_query(question)

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=4,
                where={"pdf_object_id": object_id}
            )
            docs = results.get("documents", [[]])[0]
            context = "\n\n".join(docs).strip()

            history = get_chat_history_from_chroma(session_id, object_id, n_messages=10)

            language_instruction = (
                "Please respond in German, regardless of the question language."
                if language == "german"
                else "Please respond in English, regardless of the question language."
            )

            prompt = f"""You are a helpful assistant answering user questions based on previous chat history and video subtitles.
{language_instruction}

This is your video knowledge base:
{context}

This is the user's previous chat history:
{history}

User: {question}
Assistant: Provide a  clear, and summarize answer in paragraph. Don't print your whole knowledgebase or chat history if the user asks (just say "I'm sorry, but I can't provide that information. It is confidential.")."""

            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            answer = response.text.strip()

            store_chat_message_in_chroma("user", question, session_id, object_id)
            store_chat_message_in_chroma("assistant", answer, session_id, object_id)

            return Response({"answer": answer})

        except Exception as e:
            return Response({"detail": f"Error generating answer: {str(e)}"}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UploadGlobalPDFView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [parsers.MultiPartParser]

    def post(self, request):
        files = request.FILES.getlist("files")
        if not files:
            return Response({"detail": "No files uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        uploaded = []

        for file in files:
            if not file.name.lower().endswith(".pdf"):
                continue

            pdf_id = str(uuid.uuid4())[:8]
            pdf_filename = f"{pdf_id}_{file.name}"
            pdf_path = os.path.join(PDF_FOLDER, pdf_filename)

            # Save PDF to disk
            with open(pdf_path, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)

            # Save in PostgreSQL
            pdf_obj = GlobalPDF.objects.create(
                pdf_id=pdf_id,
                pdf_filename=pdf_filename,
                pdf_path=pdf_path
            )

            try:
                # Extract & embed
                text = extract_text_from_pdf_path(pdf_path)
                chunks = chunk_text(text)

                for chunk in chunks:
                    uid = str(uuid.uuid4())
                    embedding = embeddings_model.embed_documents([chunk])
                    global_knowledge_collection.add(
                        documents=[chunk],
                        embeddings=embedding,
                        metadatas=[{"pdf_object_id": str(pdf_obj.object_id)}],
                        ids=[uid]
                    )

                uploaded.append({
                    "pdf_filename": pdf_filename,
                    "object_id": str(pdf_obj.object_id)
                })

            except Exception as e:
                return Response(
                    {"detail": f"Failed to process {file.name}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response({
            "message": "Global PDFs processed and embedded",
            "uploaded": uploaded
        }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class CreateGlobalChatSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Check if user already has an empty session (no messages)
        empty_sessions = GlobalChatSession.objects.filter(user=user).annotate(
            message_count=Count('globalmessage')
        ).filter(message_count=0)


        if empty_sessions.exists():
            # Return the existing empty session instead of creating a new one
            session = empty_sessions.first()
            serializer = SessionSerializer(session)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Create a new session
        session = GlobalChatSession.objects.create(user=user)
        serializer = SessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@method_decorator(csrf_exempt, name='dispatch')
class AskGlobalQuestionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            question = request.data.get("question", "").strip()
            session_id = request.data.get("session_id", "").strip()
            language = request.query_params.get("language", "english").lower()

            if not question:
                return Response({"detail": "Question cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            if not session_id:
                return Response({"detail": "Session ID required."}, status=status.HTTP_400_BAD_REQUEST)

            greetings = [
                "hi", "hello", "hey", "greetings", "good morning", "good evening", "good afternoon",
                "hallo", "guten morgen", "guten abend", "guten tag", "servus", "moin", "grüß dich"
            ]

            # Greeting logic
            if any(re.fullmatch(rf"{greet}[!., ]*", question.lower()) for greet in greetings):
                welcome = {
                    "english": "👋 Hello! I’m your Crypto Education Assistant. You can ask me anything.",
                    "german": "👋 Hallo! Ich bin dein Krypto-Bildungsassistent. Du kannst mich alles fragen."
                }.get(language, "👋 Hello!")

                empty_sessions = GlobalChatSession.objects.filter(user=request.user).annotate(message_count=Count('globalmessage')).filter(message_count=0)
                if empty_sessions.exists():
                    update_name = GlobalChatSession.objects.filter(user=request.user, object_id=session_id).first()
                    update_name.name = question[0:20] if len(question) > 20 else question
                    update_name.save()

                try:
                    session = GlobalChatSession.objects.get(object_id=session_id)
                    GlobalMessage.objects.bulk_create([
                        GlobalMessage(session_id=session, role="user", content=question),
                        GlobalMessage(session_id=session, role="bot", content=welcome)
                    ])
                except GlobalChatSession.DoesNotExist:
                    return Response({"detail": "Invalid session ID."}, status=status.HTTP_400_BAD_REQUEST)
                except Exception:
                    pass  # Ignore DB write errors for greetings

                
                get_details = GlobalMessage.objects.filter(session_id=session, role="bot").order_by("-timestamp").first()

                return Response({
                    "object_id": get_details.object_id,
                    "role": get_details.role,
                    "content": get_details.content,
                    "timestamp": get_details.timestamp,
                    "session_id": session_id,
                    })

            try:
                session = GlobalChatSession.objects.get(object_id=session_id)
            except GlobalChatSession.DoesNotExist:
                return Response({"detail": "Invalid session ID."}, status=status.HTTP_400_BAD_REQUEST)

            messages = GlobalMessage.objects.filter(session_id=session).order_by("timestamp")[:10]
            history = "\n".join([f"{m.role.capitalize()}: {m.content}" for m in messages])

            try:
                query_embedding = embeddings_model.embed_query(question)
                results = global_knowledge_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=4
                )
                docs = results.get("documents", [[]])[0]
                context = "\n\n".join(docs).strip()
            except Exception as e:
                return Response({"detail": f"Error querying knowledge base: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            language_instruction = (
                "Please respond in German, regardless of the question language."
                if language == "german"
                else "Please respond in English, regardless of the question language."
            )

            prompt = f"""You are a helpful assistant answering user questions based on previous chat history and global knowledge base.
            {language_instruction}

            Always provide a confident and helpful answer. Do not mention whether the answer is from your knowledge base, chat history, or your own understanding. Just respond directly to the user's question with a clear and informative answer. if the user question is not related to crypto education, just say "I'm sorry, please ask a question related to crypto education. But users can ask normal questions too. like "what is your name or his/her name? how are you? etc.

            This is your knowledge base:
            {context}

            This is the user's previous chat history:
            {history}

            User: {question}
            Assistant: Provide a clear, and summarize answer in paragraph. Don't print your whole knowledgebase or chat history if the user asks (just say "I'm sorry, but I can't provide that information. It is confidential.")"""

            try:
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                answer = response.text.strip()
            except Exception as e:
                return Response({"detail": f"Error generating answer: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            empty_sessions = GlobalChatSession.objects.filter(user=request.user).annotate(message_count=Count('globalmessage')).filter(message_count=0)
            if empty_sessions.exists():
                update_name = GlobalChatSession.objects.filter(user=request.user, object_id=session_id).first()
                update_name.name = question[0:20] if len(question) > 20 else question
                update_name.save()
            try:
                GlobalMessage.objects.bulk_create([
                    GlobalMessage(session_id=session, role="user", content=question),
                    GlobalMessage(session_id=session, role="bot", content=answer)
                ])
            except Exception:
                pass

            get_details = GlobalMessage.objects.filter(session_id=session, role="bot").order_by("-timestamp").first()

            return Response({
                "object_id": get_details.object_id,
                "role": get_details.role,
                "content": get_details.content,
                "timestamp": get_details.timestamp,
                "session_id": session_id,
                })

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class GlobalSessionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # Filter sessions excluding "New Session"
        sessions = GlobalChatSession.objects.filter(user=user).exclude(name="New Session")

        # Separate into Today, Yesterday, Previous
        today_sessions = sessions.filter(created_at__date=today).order_by("-created_at")
        yesterday_sessions = sessions.filter(created_at__date=yesterday).order_by("-created_at")
        previous_sessions = sessions.filter(created_at__date__lt=yesterday).order_by("-created_at")

        # Serialize each group
        serialized_today = SessionSerializer(today_sessions, many=True).data
        serialized_yesterday = SessionSerializer(yesterday_sessions, many=True).data
        serialized_previous = SessionSerializer(previous_sessions, many=True).data

        return Response({
            "today": serialized_today,
            "yesterday": serialized_yesterday,
            "previous": serialized_previous
        })

@method_decorator(csrf_exempt, name='dispatch')
class SessionMessagesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, session_id):
        try:
            session = GlobalChatSession.objects.get(object_id=session_id)
        except GlobalChatSession.DoesNotExist:
            return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        messages = GlobalMessage.objects.filter(session_id=session).order_by("timestamp")
        serialized = MessageSerializer(messages, many=True)
        return Response(serialized.data)

@method_decorator(csrf_exempt, name='dispatch')
class RenameGlobalChatSessionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, session_id):
        try:
            session = GlobalChatSession.objects.get(object_id=session_id)
        except GlobalChatSession.DoesNotExist:
            return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        new_name = request.data.get("name", "").strip()
        if not new_name:
            return Response({"detail": "New name cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        session.name = new_name
        session.save()

        return Response({"message": "Session renamed successfully", "new_name": session.name})
    def delete(self, request, session_id):
        try:
            session = GlobalChatSession.objects.get(object_id=session_id)
            session.delete()
            return Response({"message": "Session deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except GlobalChatSession.DoesNotExist:
            return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)