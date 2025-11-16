# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Make port 8000 available
EXPOSE 8000

# Run the service
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]
