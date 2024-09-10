# Use an appropriate base image, such as Python 3.9
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend and frontend directory
COPY backend /app/backend
COPY frontend /app/frontend

# Set environment variable for PYTHONPATH
ENV PYTHONPATH=/app/backend

# Run the application (adjust as needed)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
