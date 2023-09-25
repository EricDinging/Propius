FROM python:3.9

WORKDIR /
RUN mkdir evaluation
RUN mkdir evaluation/job
RUN mkdir propius

COPY ./evaluation/job/channels evaluation/job/channels
COPY ./evaluation/requirements_peripheral.txt evaluation/requirements_peripheral.txt
COPY ./propius propius
COPY ./evaluation/commons.py evaluation/commons.py
COPY ./propius/channels propius/channels

RUN pip install --upgrade pip
RUN pip install -r evaluation/requirements_peripheral.txt
ENTRYPOINT ["/evaluation/client/entrypoint.sh"]