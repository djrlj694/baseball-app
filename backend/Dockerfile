FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
# /bin/sh is available by default in python:3.13-slim
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
