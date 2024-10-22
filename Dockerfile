FROM ubuntu:22.04

RUN apt update
RUN apt -y install python3 python3-pip
RUN pip3 install requests

COPY . /code/

WORKDIR /code


CMD ["python3", "main.py"]