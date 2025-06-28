FROM python:3.12-slim

# Install required tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-spa \
        poppler-utils ffmpeg calibre curl tar && \
    rm -rf /var/lib/apt/lists/*

# Download Piper executable for the correct architecture
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        PIPER_URL="https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"; \
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
        PIPER_URL="https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz"; \
    else \
        echo "Unsupported architecture: $ARCH"; \
        exit 1; \
    fi && \
    curl -L -o /tmp/piper.tar.gz "$PIPER_URL" && \
    tar -xzf /tmp/piper.tar.gz -C /usr/local/bin piper && \
    chmod +x /usr/local/bin/piper && \
    rm /tmp/piper.tar.gz

# Environment variables used by the app
ENV TESSERACT_CMD_PATH=/usr/bin/tesseract \
    CALIBRE_EBOOK_CONVERT_PATH=/usr/bin/ebook-convert \
    POPPLER_PATH=/usr/bin \
    PIPER_EXECUTABLE_PATH=/usr/local/bin/piper/piper

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