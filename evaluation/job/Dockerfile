FROM python:3.9

WORKDIR /
RUN mkdir /evaluation

COPY ./evaluation/requirements_peripheral.txt /evaluation/requirements_peripheral.txt
COPY ./propius_job /propius_job
COPY ./evaluation/commons.py /evaluation/commons.py
COPY ./evaluation/executor/channels /evaluation/executor/channels

RUN pip install --upgrade pip
RUN pip install -r /evaluation/requirements_peripheral.txt
CMD ["python", "./evaluation/job/job_dispatcher.py"]