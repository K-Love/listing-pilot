FROM python:3.11-slim

LABEL org.opencontainers.image.title="KeyProse"
LABEL org.opencontainers.image.description="KeyProse: the AI back office for listing agents"

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

ENV PYTHONPATH=/app/backend
ENV PORT=8000
EXPOSE 8000

CMD ["python", "backend/server.py"]
