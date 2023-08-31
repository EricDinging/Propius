FROM python:3.9

WORKDIR /
RUN mkdir propius

COPY ./propius/channels propius/channels
COPY ./propius/util propius/util
COPY ./propius/database /propius/database

COPY ./propius/requirements.txt propius/requirements.txt

RUN pip3 install -r propius/requirements.txt

CMD ["python", "propius/load_balancer/load_balancer.py"]