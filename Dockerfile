# Use the official Ubuntu 22.04 LTS as the base image
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install essential packages
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    build-essential && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.12 \
        python3.12-venv \
        python3.12-dev \
        libtesseract-dev \
        ghostscript \
        poppler-utils \
        ffmpeg \
        tesseract-ocr && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    python3.12 get-pip.py && \
    rm get-pip.py && \
    python3.12 -m pip install --upgrade pip && \
    python3.12 -m pip install \
        Pillow \
        rembg[cpu] \
        ffmpeg-python \
        pytesseract \
        PyPDF2 \
        pdf2image \
	python-docx \
	python-telegram-bot \
        opencv-python && \
    mkdir $HOME/.u2net && \
    wget -O $HOME/.u2net/isnet-general-use.onnx https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx && \
    ln -sf /usr/bin/python3.12 /usr/local/bin/python3 && \
    ln -sf /usr/local/bin/pip3 /usr/local/bin/pip && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Specify the default command to run when starting the container
CMD ["bash"]
