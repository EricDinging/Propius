FROM python:3.9

WORKDIR /
RUN mkdir propius

COPY ./propius/client_manager propius/client_manager
COPY ./propius/channels propius/channels
COPY ./propius/util propius/util

COPY ./propius/requirements.txt propius/requirements.txt

RUN pip3 install -r propius/requirements.txt

CMD ["python", "propius/client_manager/client_manager.py", "0"]