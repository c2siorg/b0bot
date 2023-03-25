FROM python:3.8-bullseye

# Set the working directory to /app
WORKDIR /code

# Copy the requirements file and install the dependencies
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY ./src ./src

# Expose port 80 to the outside world
EXPOSE 80

# Start the Flask application
# development mode
CMD ["gunicorn", "-b", "0.0.0.0:80", "--log-level", "debug", "--reload", "src.app:app"]  
# production mode
# CMD ["gunicorn", "-b", "0.0.0.0:80","src.app:app"]