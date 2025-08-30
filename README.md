# Presidio FastAPI Masker & Image Redactor

A FastAPI service for text anonymization (using Presidio) and image redaction, ready for local or public (tunneled) hosting.

---

## 🌐 Hosting

### Localhost (Development)
Run locally:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
Access at: [http://localhost:8000](http://localhost:8000)

### Public Tunnel (localhost.run)
Expose your local server to the internet:
```bash
ssh -i ~/.ssh/id_app2 -R 80:localhost:8000 localhost.run
```
You’ll get a public URL like: `https://xxxxxx.lhr.life`

---

## 🚀 Base URL

All API requests should be prefixed with the base URL.

- **Development**: `http://localhost:8000`
- **Tunnel/Public**: `https://xxxxxx.lhr.life`

---

## 📝 API Endpoints

### `POST /mask`
Mask sensitive entities in text with `<ENTITY_TYPE>`.

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "My name is John Doe, call me at 555-123-4567"}
  ]
}
```
**Response:**
```json
{
  "messages": [
    {"role": "user", "content": "My name is <PERSON>, call me at <PHONE_NUMBER>"}
  ]
}
```

---

### `POST /replace`
Replace sensitive entities in text with custom values.

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "My name is John Doe, call me at 555-123-4567"}
  ]
}
```
**Response:**
```json
{
  "messages": [
    {"role": "user", "content": "My name is ABC, call me at 0000000"}
  ]
}
```

---

### `POST /redact_image_url`
Redact sensitive info from an image by URL.

**Request Body:**
```json
{
  "image_url": "https://example.com/your_image.png"
}
```
**Response:**
```json
{
  "redacted_image_url": "https://xxxxxx.lhr.life/output/redacted_YYYYMMDD_HHMMSS_xxxxxx.png"
}
```

---

### `POST /redact_image_base64`
Redact sensitive info from a base64-encoded image.

**Request Body:**
```json
{
  "image_b64": "<base64-encoded-image>"
}
```
**Response:**
```json
{
  "redacted_image_url": "https://xxxxxx.lhr.life/output/redacted_YYYYMMDD_HHMMSS_xxxxxx.png"
}
```

---

## 🛠️ Example cURL

```bash
curl -X POST https://xxxxxx.lhr.life/replace \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"My name is John Doe, call me at 555-123-4567"}]}'
```

---

## 📦 Requirements

- Python 3.9+
- Docker (optional)
- Presidio, spaCy, Tesseract (see Dockerfile for setup)

---

## 🔑 Notes
- For a stable public URL, use a persistent tunnel with your SSH key and localhost.run account.
- All output images are saved in the `output` folder and served at `/output/<filename>`.

---

## License
MIT
