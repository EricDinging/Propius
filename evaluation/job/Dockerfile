FROM python:3.9

WORKDIR /
RUN mkdir evaluation
RUN mkdir propius

COPY ./evaluation/requirements_peripheral.txt evaluation/requirements_peripheral.txt

RUN pip install --upgrade pip
RUN pip install -r evaluation/requirements_peripheral.txt
ENTRYPOINT ["/evaluation/job/entrypoint.sh"]