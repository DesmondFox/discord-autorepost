FROM python:3.11-slim
WORKDIR /app
COPY bot ./bot
COPY main.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
