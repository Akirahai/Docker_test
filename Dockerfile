FROM python:3.9.23-trixie

WORKDIR /app

COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Install spaCy English large model
RUN python -m spacy download en_core_web_lg

# Download Tesseract AppImage to /app/bin and make it executable
RUN mkdir -p /app/bin && \
		wget -O /app/bin/tesseract.AppImage \
			https://github.com/AlexanderP/tesseract-appimage/releases/download/v5.5.1/tesseract-5.5.1-x86_64.AppImage && \
		chmod +x /app/bin/tesseract.AppImage

# Add /app/bin to PATH
ENV PATH="/app/bin:$PATH"


COPY . .

CMD uvicorn main:app