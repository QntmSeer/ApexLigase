# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies for MDTraj and Matplotlib
RUN apt-get update && apt-get install -y \
    build-essential \
    libfftw3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core analysis pipeline
COPY analyze_apex.py .
COPY premium_plots.py .
COPY assets/ ./assets/

# Default command
CMD ["python", "analyze_apex.py"]
