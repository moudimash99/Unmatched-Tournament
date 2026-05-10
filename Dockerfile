FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY tournament_a.html .

EXPOSE 8742

CMD ["python", "app.py"]
