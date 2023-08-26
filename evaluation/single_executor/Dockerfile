# FROM nvidia/cuda:11.6-base
# RUN apt-get update && \
#     apt-get install -y python3 python3-pip

FROM python:3.9

WORKDIR /
RUN mkdir /evaluation
COPY ./evaluation/evaluation_config.yml /evaluation/evaluation_config.yml
COPY ./evaluation/single_executor /evaluation/single_executor
COPY ./evaluation/commons.py /evaluation/commons.py

COPY ./evaluation/requirements.txt /evaluation/requirements.txt

RUN pip3 install -r /propius/requirements.txt
CMD ["python", "./evaluation/single_executor/single_executor.py"]