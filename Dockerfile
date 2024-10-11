# syntax=docker/dockerfile:1
ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
RUN rm /usr/lib/python*/EXTERNALLY-MANAGED && \
    python3 -m ensurepip && \
    pip3 install flask requests


# Set environment variables
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Set working directory
# WORKDIR /app

ENV NODE_ENV=production

# Expose port 5000
EXPOSE 5000/tcp

# Copy the workout data script
# COPY workout_data.py /

# Copy the startup script
COPY run.sh /

# Make the run.sh script executable
# RUN chmod +x /run.sh
RUN chmod a+x /run.sh
# Start the Flask server
CMD ["/run.sh"]
