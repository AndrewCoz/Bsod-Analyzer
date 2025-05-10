FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bsod-analyzer-python/ ./bsod-analyzer-python/
COPY error-codes.json ./
COPY frontend/ ./frontend/

WORKDIR /app/bsod-analyzer-python
EXPOSE 5000

# Use environment variable for port
ENV PORT=5000

# Use waitress for production
CMD ["python", "deploy.py"] 