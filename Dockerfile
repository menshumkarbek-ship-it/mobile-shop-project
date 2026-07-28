# Use an explicit lightweight optimized official Python image layer
FROM python:3.11-slim

# Prevent Python from writing pyc cache dumps to tracking disks
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establish isolated internal workspace folder
WORKDIR /app

# Install native compilation requirements for packages like psycopg2 or Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Pipe dependencies tracking configuration files internally
COPY requirements.txt /app/

# Install execution layer modules globally inside container spaces
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy absolute current directory workspace contents internally
COPY . /app/