# FROM nvidia/cuda:11.6-base
# RUN apt-get update && \
#     apt-get install -y python3 python3-pip

FROM python:3.9

WORKDIR /
RUN mkdir /evaluation
COPY ./evaluation/commons.py /evaluation/commons.py
COPY ./fedscale /fedscale
COPY ./evaluation/requirements.txt /evaluation/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /evaluation/requirements.txt
CMD ["python", "./evaluation/single_executor/executor.py"]