from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status,permissions
from .models import *
import uuid
from .serializers import *
from .utils import *
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import NotFound, APIException
from rest_framework.permissions import IsAuthenticated



class UploadVideo(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("video")
        if not file:
            return Response({"detail": "No video file uploaded."}, status=400)

        video_id = str(uuid.uuid4())[:8]

        # Create video entry with file
        video = Video.objects.create(
            video_id=video_id,
            file=file,
        )

        # Save filename and path after file is uploaded
        video.video_filename = video.file.name.split('/')[-1]
        video.video_path = video.file.name  # This is relative to MEDIA_ROOT
        video.save()

        return Response({
            "message": "Video uploaded successfully",
            "video_id": video.video_id,
            "object_id": str(video.object_id),
            "video_filename": video.video_filename,
            "video_path": video.video_path,
            "next_step": f"/api/v1/ai/process_video/{video.object_id}/"
        })
    


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
class ProcessFromFileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, object_id):
        try:
            pdf_path, pdf_filename, subtitle_object_id = process_video_from_file(object_id)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "pdf_path": pdf_path,
            "pdf_filename": pdf_filename,
            "subtitle_object_id": str(subtitle_object_id)
        })



@method_decorator(csrf_exempt, name='dispatch')
class LoadPDFPostgresToChroma(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, object_id):
        print(f"Received object_id: {object_id}")
        try:
            # ✅ Fetch subtitle object from PostgreSQL using UUID
            try:
                subtitle = Subtitle.objects.get(object_id=object_id)
            except Subtitle.DoesNotExist:
                raise NotFound("Subtitle document not found in PostgreSQL")

            pdf_filename = subtitle.pdf_filename
            if not pdf_filename:
                raise NotFound("PDF filename not found in Subtitle record")

            pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
            print(f"PDF Path: {pdf_path}")
            if not os.path.exists(pdf_path):
                raise NotFound("PDF file not found on server")

            # ✅ Extract, chunk, and store text
            text = extract_text_from_pdf_path(pdf_path)
            chunks = chunk_text(text)
            store_embeddings_for_pdf(str(subtitle.object_id), chunks)

            return Response({
                "message": f"PDF text embedded and stored in ChromaDB for object_id {subtitle.object_id}"
            })

        except Exception as e:
            raise APIException(f"Error processing PDF from PostgreSQL: {str(e)}")

import random
import string

def generate_session_id(length=12):
    """Generates a random alphanumeric session ID."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class CreateVideoChatSession(APIView):

    def post(self, request):
        session_id = generate_session_id()
        return Response({
            "session_id": session_id,
            "message": "Session created successfully"
        })

import uuid

def store_chat_message_in_chroma(role: str, content: str, session_id: str, video_object_id: str):
    embedding = embeddings_model.embed_documents([content])
    uid = str(uuid.uuid4())
    video_chat_collection.add(
        documents=[content],
        embeddings=embedding,
        metadatas=[{
            "role": role,
            "session_id": session_id,
            "video_object_id": video_object_id
        }],
        ids=[uid]
    )



def get_chat_history_from_chroma(session_id: str, video_object_id: str, n_messages: int = 6):
    results = video_chat_collection.get(
        where={"session_id": session_id}
    )

    if not results or "documents" not in results:
        return ""

    # Reconstruct chat turns and sort by insertion order (Chroma preserves it)
    docs = results["documents"]
    metas = results["metadatas"]

    messages = []
    for doc, meta in zip(docs, metas):
        if meta.get("video_object_id") == video_object_id:
            role = meta.get("role", "user").capitalize()
            messages.append(f"{role}: {doc.strip()}")

    # Return last N messages
    print(messages[-n_messages:])
    return "\n".join(messages[-n_messages:])




import google.generativeai as genai
import re

@method_decorator(csrf_exempt, name='dispatch')  # disable CSRF if needed
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
                welcome_message = welcome_de if language == "de" else welcome_en

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
                if language == "de"
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
        
from rest_framework import status, permissions, parsers

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


from django.db.models import Count

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

    



class AskGlobalQuestionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            question = request.data.get("question", "").strip()
            session_id = request.data.get("session_id", "").strip()
            language = request.query_params.get("language", "en").lower()

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
                    "en": "👋 Hello! I’m your Crypto Education Assistant. You can ask me anything.",
                    "de": "👋 Hallo! Ich bin dein Krypto-Bildungsassistent. Du kannst mich alles fragen."
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

                return Response({"answer": welcome})

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
                if language == "de"
                else "Please respond in English, regardless of the question language."
            )

            prompt = f"""You are a helpful assistant answering user questions based on previous chat history and global knowledge base.
            {language_instruction}

            Don't give answer if you don't have information on your knowledgebase or chat history. Don't use your own thinking if information is not available in your knowledgebase or chat history.

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

            return Response({"answer": answer})

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class GlobalSessionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        sessions = GlobalChatSession.objects.filter(user=user).exclude(name="New Session").order_by("-created_at")
        serialized = SessionSerializer(sessions, many=True)
        return Response(serialized.data)
    


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