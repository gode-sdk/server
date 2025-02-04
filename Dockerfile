FROM python:3.9-slim
RUN apt-get update && apt-get install -y libpq-dev
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r docker-requirements.txt
COPY . /app/
CMD ["python", "main.py"]