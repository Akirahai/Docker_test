from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer.entities import OperatorConfig
from fastapi import UploadFile, File
import os
import io
from typing import Dict
from image_redact_utils import redact_image_from_base64, redact_image_from_url

# Initialize Presidio engines once
anonymizer = AnonymizerEngine()
analyzer = AnalyzerEngine()

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

# Custom replacement values for each entity type
ENTITY_REPLACEMENTS = {
    "PERSON": "ABC",
    "PHONE_NUMBER": "0000000",
    "EMAIL_ADDRESS": "example@gmail.com",
    "US_SSN": "000-00-0000",
    "CREDIT_CARD": "0000-0000-0000-0000",
    "IP_ADDRESS": "192.168.1.1",
    "LOCATION": "Anytown",
    "URL": "https://example.com",
    "DATE_TIME": "2023-01-01",
    "CRYPTO": "abc123",
    "US_PASSPORT": "000000000",
    "US_BANK_NUMBER": "000000000",
    "US_DRIVER_LICENSE": "D000000000",
    "IBAN_CODE": "GB00 0000 0000 0000 0000 00",
    "UK_NHS": "000 000 0000",
    "US_ITIN": "000-00-0000",
    "MEDICAL_LICENSE": "ML000000",
    "NRP": "000000000"
}

FULL_ENTITIES = ['CRYPTO', 'US_PASSPORT', 'DATE_TIME', 'EMAIL_ADDRESS', 'URL', 'US_BANK_NUMBER', 'US_DRIVER_LICENSE', 'IBAN_CODE', 'UK_NHS', 'US_ITIN', 'CREDIT_CARD', 'IP_ADDRESS', 'PERSON', 'PHONE_NUMBER', 'MEDICAL_LICENSE', 'US_SSN', 'LOCATION', 'NRP']


def presidio_anonymize(data: dict, use_custom_replacements: bool = False) -> dict:
    """
    Anonymize sensitive information sent by the user or returned by the model.
    Works for structures with either:
      - {"messages":[{role, content}, ...]}
      - {"choices":[{"message":{role, content}}, ...]}
    
    Args:
        data: The input data containing messages or choices
        use_custom_replacements: If True, uses custom replacement values. If False, uses default <ENTITY_TYPE> format
    """
    message_list = (
        data.get("messages") or [data.get("choices", [{}])[0].get("message")]
    )

    if not message_list or not all(isinstance(msg, dict) and msg for msg in message_list):
        return data

    for message in message_list:
        content = message.get("content", "")
        if not content.strip():
            continue

        results = analyzer.analyze(
            text=content,
            entities= FULL_ENTITIES,
            language="en",
        )
        
        if use_custom_replacements:
            # Create operator configs for custom replacements
            operators = {}
            for result in results:
                entity_type = result.entity_type
                if entity_type in ENTITY_REPLACEMENTS:
                    operators[entity_type] = OperatorConfig("replace", {"new_value": ENTITY_REPLACEMENTS[entity_type]})
            
            anonymized_result = anonymizer.anonymize(
                text=content,
                analyzer_results=results,
                operators=operators,
            )
        else:
            # Use default masking (<ENTITY_TYPE> format)
            anonymized_result = anonymizer.anonymize(
                text=content,
                analyzer_results=results,
            )
        
        message["content"] = anonymized_result.text

    return data


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
