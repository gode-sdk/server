# Use an official Python base image
FROM python:3.9-slim

# Install PostgreSQL development libraries (to provide pg_config)
RUN apt-get update && apt-get install -y libpq-dev

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt into the container (ensure it's the correct filename)
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app/

# Set the command to run your application
CMD ["python", "main.py"]
