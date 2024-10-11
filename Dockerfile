FROM python:3.10-slim

# Set environment variables
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Install necessary packages
RUN pip install flask requests

# Copy the workout data script
COPY workout_data.py /app/workout_data.py

# Copy the startup script
COPY run.sh /app/run.sh

# Set working directory
WORKDIR /app

# Make the run.sh script executable
RUN chmod +x /app/run.sh

# Expose port 5000
EXPOSE 5000

# Start the Flask server
CMD ["/app/run.sh"]
