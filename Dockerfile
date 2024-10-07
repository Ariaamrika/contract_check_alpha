# Use the official Python image as the base image
FROM python:3.9-slim

# Set environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install system dependencies for argon2-cffi
RUN apt-get update --fix-missing && apt-get install -y build-essential libffi-dev

# Copy the entire application into the container
COPY . .

# Expose the port that Streamlit will run on
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_ui_3.py"]
