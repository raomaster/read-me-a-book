FROM python:3.12-slim

# Install required tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-spa \
        poppler-utils ffmpeg calibre curl && \
    rm -rf /var/lib/apt/lists/*

# Download Piper executable
RUN curl -L -o /usr/local/bin/piper \
    https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_x86_64 \
    && chmod +x /usr/local/bin/piper

# Environment variables used by the app
ENV TESSERACT_CMD_PATH=/usr/bin/tesseract \
    CALIBRE_EBOOK_CONVERT_PATH=/usr/bin/ebook-convert \
    POPPLER_PATH=/usr/bin \
    PIPER_EXECUTABLE_PATH=/usr/local/bin/piper

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p \
        ./models/es_MX \
        ./models/es_MX \
        ./models/es_ES-mls_9972-low \
    && curl -fSL \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx \
        -o ./models/es_MX/es_MX-claude-high.onnx \
    && curl -fSL \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx.json \
        -o ./models/es_MX/es_MX-claude-high.json \
    && curl -fSL \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx \
        -o ./models/es_MX/es_MX-ald-medium.onnx \
    && curl -fSL \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx.json \
        -o ./models/es_MX/es_MX-ald-medium.json \
    && curl -fSL \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_9972/low/es_ES-mls_9972-low.onnx \
        -o ./models/es_ES-mls_9972-low/es_ES-mls_9972-low.onnx \
    && curl -fSL \
        https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_9972/low/es_ES-mls_9972-low.onnx.json \
        -o ./models/es_ES-mls_9972-low/es_ES-mls_9972-low.json



EXPOSE 8000
#CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["python", "-m", "src.main"]