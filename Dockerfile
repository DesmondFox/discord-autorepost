FROM python:3.11-slim
WORKDIR /app
COPY main.py .
COPY local_file.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]