FROM python:3.11-bullseye

ENV PYTHONUNBUFFERED 1
ADD requirements.txt /requirements.txt
RUN apt update && apt install -y libhdf5-dev
RUN pip install -r /requirements.txt

ADD . /src
WORKDIR /src
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install poppler-utils -y

EXPOSE 8008

CMD ["python", "manage.py", "runserver", "0.0.0.0:8008"]

