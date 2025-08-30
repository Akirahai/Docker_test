
import os
import base64
import io
from datetime import datetime
from fastapi import UploadFile
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = "/home/long_2/hai/fastapi_docker/.venv/bin/tesseract.AppImage"
from presidio_image_redactor import ImageRedactorEngine

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

engine = ImageRedactorEngine()

def save_redacted_image(image: Image.Image) -> str:
    """Save redacted image to output folder with timestamped filename and return the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = os.path.join(OUTPUT_DIR, f"redacted_{timestamp}.png")
    image.save(output_path)
    return output_path

def redact_image_from_base64(b64_string: str) -> str:
    """Redact an image from a base64 string and return the output path."""
    image_data = base64.b64decode(b64_string)
    image = Image.open(io.BytesIO(image_data))
    redacted_image = engine.redact(image, language="en")
    return save_redacted_image(redacted_image)

def redact_image_from_url(url: str) -> str:
    """Redact an image from a URL and return the output path."""
    import requests
    response = requests.get(url)
    image = Image.open(io.BytesIO(response.content))
    redacted_image = engine.redact(image, language="en")
    return save_redacted_image(redacted_image)

def redact_image_from_upload(upload_file: UploadFile) -> str:
    """Redact an image from an uploaded file and return the output path."""
    image = Image.open(upload_file.file)
    redacted_image = engine.redact(image, language="en")
    return save_redacted_image(redacted_image)
