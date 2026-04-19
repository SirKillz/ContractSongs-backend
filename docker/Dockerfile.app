# Use the base python image
FROM python:3.12

# Set the working directory
WORKDIR /app

# COPY the Requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.__main__:app", "--host", "0.0.0.0", "--port", "8000", "--reload","--reload-dir", "/app/app"]