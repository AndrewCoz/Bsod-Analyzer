FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bsod-analyzer-python/ ./bsod-analyzer-python/
COPY error-codes.json ./
COPY frontend/ ./frontend/

WORKDIR /app/bsod-analyzer-python
EXPOSE 5000

CMD ["python", "deploy.py"] 