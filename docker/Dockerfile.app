# Use the base python image
FROM python:3.13

# Install ffmpeg
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# COPY the Requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy input audio directory (with your mp3)
COPY contract-song-audio-in ./contract-song-audio-in

# Create output directory
RUN mkdir -p /app/contract-song-audio-out

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.__main__:app", "--host", "0.0.0.0", "--port", "8000", "--reload","--reload-dir", "/app/app"]