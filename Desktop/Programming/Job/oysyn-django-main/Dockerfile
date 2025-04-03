# Use official Python image as a base
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Install PostgreSQL client utilities
RUN apt-get update && apt-get install -y postgresql-client

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader stopwords punkt punkt_tab

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

# Expose the port that Django will run on
EXPOSE 8000

# Start the Django application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]

RUN pip install Pillow