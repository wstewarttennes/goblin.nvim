FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

# Set the working directory
WORKDIR /app

# Copy the content of the repository to the working directory
COPY ./ /app

# Change the environment variable to the desired port
ENV PORT=8008

RUN apt-get update && \
    apt-get install -y libhdf5-dev && \
    apt-get clean

RUN pip install -r requirements.txt

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008", "--reload"]
