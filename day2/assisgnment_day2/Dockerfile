FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY assday2.py .

EXPOSE 8000

CMD ["uvicorn", "assday2:app", "--host", "0.0.0.0", "--port", "8000"]
