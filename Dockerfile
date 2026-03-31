# Dockerfile

# --- Stage 1: Build Stage ---
# Use an official Python runtime as a parent image
FROM python:3.10-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install Gunicorn
RUN pip install gunicorn

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install dependencies into a temporary folder (wheels)
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# --- Stage 2: Final Stage ---
# Use a slim, non-root base image for the final application
FROM python:3.10-slim

# Create a non-root user to run the application
RUN addgroup --system app && adduser --system --group app

# Set the working directory
WORKDIR /app

# Copy the installed wheels from the builder stage
COPY --from=builder /app/wheels /wheels

# Install the dependencies from the wheels
RUN pip install --no-cache /wheels/*

# Copy the application code into the container
COPY . .

# Change the owner of the application directory to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application using Gunicorn and Uvicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main:app"]