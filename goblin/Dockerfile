FROM python:3.11-bullseye
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libhdf5-dev \
    libmagic1 \
    poppler-utils \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# Add project files
ADD . /src
WORKDIR /src

EXPOSE 8011
