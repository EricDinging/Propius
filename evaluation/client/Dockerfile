FROM python:3.9

WORKDIR /
RUN mkdir /evaluation
RUN mkdir /evaluation/job

COPY ./evaluation/job/channels /evaluation/job/channels
COPY ./evaluation/requirements_peripheral.txt /evaluation/requirements_peripheral.txt
COPY ./propius_client /propius_client
COPY ./evaluation/commons.py /evaluation/commons.py

RUN pip install --upgrade pip
RUN pip install -r /evaluation/requirements_peripheral.txt
CMD ["python", "./evaluation/client/client_dispatcher.py"]