FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash vidarchive

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
RUN pip install --no-cache-dir -e .

USER vidarchive

EXPOSE 5000

ENV VIDARCHIVE_OUTPUT_DIR=/downloads

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "600", "vidarchive.wsgi:app"]
