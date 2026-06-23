# Hugging Face Spaces (Docker SDK) expects the app to listen on port 7860.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# DEV_MODE caching writes to .cache/; keep it off in the hosted app.
ENV DEV_MODE=0
EXPOSE 7860

CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "7860"]
