FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-ara poppler-utils libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements-runtime.txt requirements-runtime.txt
RUN pip install --no-cache-dir -r requirements-runtime.txt
COPY . .
RUN useradd --create-home --shell /usr/sbin/nologin fulaw && mkdir -p /data && chown -R fulaw:fulaw /app /data
USER fulaw
ENV FUHRER_DATA_DIR=/data
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
