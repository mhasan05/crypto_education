import os
from datetime import datetime
from .models import Video, Subtitle
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from fpdf import FPDF
import ffmpeg
import whisper
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
    video_path = video_obj.video_path
    video_filename = video_obj.video_filename

    if not os.path.exists(video_path):
        raise Exception("Video file not found")

    # Extract original filename without video_id prefix
    original_filename = "_".join(video_filename.split("_")[1:])

    audio_path = os.path.splitext(video_path)[0] + ".wav"
    extract_audio(video_path, audio_path)
    segments = transcribe_whisper(audio_path)
    os.remove(audio_path)

    pdf = UnicodePDF(video_id, str(video_obj.id), original_filename)
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

    subtitle_obj = Subtitle.objects.create(
        video=video_obj,
        video_filename=original_filename,
        pdf_filename=pdf_filename,
        transcript=segments,
        created_at=datetime.utcnow()
    )

    return pdf_path, pdf_filename, subtitle_obj.id
