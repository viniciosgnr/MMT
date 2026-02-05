# Use an official Python runtime as a parent image
FROM python:3.11-alpine

# Set the working directory in the container
WORKDIR /app

# Install build dependencies for postgres (psycopg2) and others
# gcc, musl-dev, postgresql-dev are needed for compiling psycopg2
# libffi-dev might be needed for other libs
RUN apk add --no-cache gcc musl-dev postgresql-dev libffi-dev

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.main:app when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
