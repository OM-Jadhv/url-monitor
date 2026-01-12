FROM python:3.11-slim

WORKDIR /app

# Create directory for database and set permissions
RUN mkdir -p /app/data && chmod 777 /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
