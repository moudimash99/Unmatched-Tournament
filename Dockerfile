FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts ./scripts
COPY generated ./generated
COPY data ./data

EXPOSE 8742

CMD ["python", "scripts/app.py"]
