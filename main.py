from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi import UploadFile, File
import os
import io
from typing import Dict
from image_redact_utils import redact_image_from_base64, redact_image_from_url
from presidio_anonymize import presidio_anonymize

app = FastAPI(title="Presidio FastAPI Masker", version="1.0.0")

# Ensure output directory exists for images
os.makedirs("output", exist_ok=True)


# Endpoint: POST /redact_image_base64
@app.post("/redact_image_base64")
async def redact_image_base64_endpoint(payload: Dict[str, str], request: Request):
    """
    Accepts a JSON payload with a base64-encoded image string under the key 'image_b64'.
    Returns a link to the redacted image.
    """
    try:
        b64_string = payload.get("image_b64")
        if not b64_string:
            raise HTTPException(status_code=400, detail="Missing 'image_b64' in request body.")
        output_path = redact_image_from_base64(b64_string)
        image_url = str(request.base_url) + f"output/{os.path.basename(output_path)}"
        return {"redacted_image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint: POST /redact_image_url
@app.post("/redact_image_url")
async def redact_image_url_endpoint(payload: Dict[str, str], request: Request):
    """
    Accepts a JSON payload with an image URL under the key 'image_url'.
    Returns a link to the redacted image.
    """
    try:
        url = payload.get("image_url")
        if not url:
            raise HTTPException(status_code=400, detail="Missing 'image_url' in request body.")
        output_path = redact_image_from_url(url)
        image_url = str(request.base_url) + f"output/{os.path.basename(output_path)}"
        return {"redacted_image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve output images statically
from fastapi.staticfiles import StaticFiles
app.mount("/output", StaticFiles(directory="output"), name="output")



@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/mask")
async def mask_endpoint(request: Request):
    """
    Mask sensitive information using default <ENTITY_TYPE> format
    """
    try:
        body = await request.json()
        masked = presidio_anonymize(body, use_custom_replacements=False)
        return JSONResponse(masked)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/replace")
async def replace_endpoint(request: Request):
    """
    Replace sensitive information with custom replacement values
    """
    try:
        body = await request.json()
        replaced = presidio_anonymize(body, use_custom_replacements=True)
        return JSONResponse(replaced)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
