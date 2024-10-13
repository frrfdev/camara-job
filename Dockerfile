# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your application's code
COPY . .

# Make port 80 available to the world outside this container
EXPOSE 80

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the script when the container launches
CMD ["python", "job.py"]
