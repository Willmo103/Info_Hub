# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /src

# Copy requirements.txt to the working directory
COPY requirements.txt /src

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /src

# Make port 5000 available to the world outside this container
EXPOSE 4202

# Define environment variable
ENV FLASK_APP=app

# Run app.py when the container launches
# CMD ["flask", "run", "port=5000", "host=0.0.0.0"]
CMD ["flask", "run", "--host=0.0.0.0", "--port=4202"]
