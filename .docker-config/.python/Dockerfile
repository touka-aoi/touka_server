FROM python:3.10.8-bullseye

WORKDIR /usr/src/app

COPY ./requirements.txt  /usr/src/app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt