FROM python:3.9

WORKDIR /
RUN mkdir propius
RUN mkdir propius/client_manager

COPY ./propius/channels propius/channels
COPY ./propius/util propius/util

COPY ./propius/requirements.txt propius/requirements.txt
COPY ./propius/client_manager/entrypoint.sh propius/client_manager/entrypoint.sh

RUN pip3 install -r propius/requirements.txt
RUN chmod +x propius/client_manager/entrypoint.sh

ENTRYPOINT ["propius/client_manager/entrypoint.sh"]