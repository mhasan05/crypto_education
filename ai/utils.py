import os
from datetime import datetime
from .models import Video, Subtitle
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from fpdf import FPDF
from PyPDF2 import PdfReader
import ffmpeg
import whisper
from langchain.text_splitter import RecursiveCharacterTextSplitter
whisper_model = whisper.load_model("base")

PDF_FOLDER = os.path.join(settings.BASE_DIR, "pdf_files")
FONT_FILE = os.path.join(settings.BASE_DIR, "fonts", "DejaVu.ttf")

def extract_audio(video_path, audio_path):
    ffmpeg.input(video_path).output(audio_path, acodec='pcm_s16le', ar='16000').run(overwrite_output=True)

def transcribe_whisper(audio_path):
    result = whisper_model.transcribe(audio_path, word_timestamps=True)
    return [{"start": seg["start"], "end": seg["end"], "text": seg["text"]} for seg in result.get("segments", [])]

def format_time(seconds):
    mins, secs = divmod(int(seconds), 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"

class UnicodePDF(FPDF):
    def __init__(self, video_id, object_id, video_filename):
        super().__init__()
        self.video_id = video_id
        self.object_id = object_id
        self.video_filename = video_filename

    def header(self):
        self.set_font("DejaVu", size=12)
        self.cell(0, 10, "Subtitles Extracted from Video", ln=True, align="C")
        self.ln(5)
        self.set_font("DejaVu", size=10)
        self.cell(0, 10, f"Video ID: {self.video_id}", ln=True, align="C")
        self.cell(0, 10, f"Object ID: {self.object_id}", ln=True, align="C")
        self.cell(0, 10, f"Video Name: {self.video_filename}", ln=True, align="C")
        self.ln(5)

def process_video_from_file(object_id: str):
    try:
        video_obj = Video.objects.get(pk=object_id)
    except ObjectDoesNotExist:
        raise Exception("Video not found")

    video_id = video_obj.video_id
    video_filename = video_obj.video_filename
    relative_video_path = video_obj.video_path

    # ✅ Combine MEDIA_ROOT with the relative path
    absolute_video_path = os.path.join(settings.MEDIA_ROOT, relative_video_path)

    if not os.path.exists(absolute_video_path):
        raise Exception("Video file not found")

    # ✅ Extract original filename (removes prefix like video_id)
    original_filename = "_".join(video_filename.split("_")[1:])

    # ✅ Extract audio and process transcription
    audio_path = os.path.splitext(absolute_video_path)[0] + ".wav"
    extract_audio(absolute_video_path, audio_path)
    segments = transcribe_whisper(audio_path)
    os.remove(audio_path)

    # ✅ Create subtitle PDF
    pdf = UnicodePDF(video_id, str(video_obj.object_id), original_filename)
    pdf.add_font("DejaVu", "", FONT_FILE, uni=True)
    pdf.set_font("DejaVu", size=12)
    pdf.add_page()

    for seg in segments:
        line = f"[{format_time(seg['start'])} - {format_time(seg['end'])}] {seg['text'].strip()}"
        pdf.multi_cell(0, 10, line)
        pdf.ln(2)

    pdf_filename = f"{os.path.splitext(original_filename)[0]}_subtitles_{video_id}.pdf"
    pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
    pdf.output(pdf_path)

    # ✅ Save to Subtitle model
    subtitle_obj = Subtitle.objects.create(
        video=video_obj,
        video_filename=original_filename,
        pdf_filename=pdf_filename,
        transcript=segments,
        created_at=datetime.utcnow()
    )

    return pdf_path, pdf_filename, subtitle_obj.object_id




def extract_text_from_pdf_path(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError("PDF file not found on server")
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text


def chunk_text(text, chunk_size=10000, chunk_overlap=1000):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

import uuid
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# ───────────── ChromaDB Setup ─────────────
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "video_pdf_knowledge"
GLOBAL_COLLECTION_NAME = "global_pdf_knowledge"
VIDEO_CHAT_COLLECTION = "video_chat_memory"



chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
global_knowledge_collection = chroma_client.get_or_create_collection(name=GLOBAL_COLLECTION_NAME)
video_chat_collection = chroma_client.get_or_create_collection(name=VIDEO_CHAT_COLLECTION)
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
def store_embeddings_for_pdf(object_id: str, text_chunks):
    for chunk in text_chunks:
        uid = str(uuid.uuid4())
        embedding = embeddings_model.embed_documents([chunk])
        collection.add(
            documents=[chunk],
            embeddings=embedding,
            metadatas=[{"pdf_object_id": object_id}],
            ids=[uid]
        )