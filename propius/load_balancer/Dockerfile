FROM python:3.9

WORKDIR /
RUN mkdir /propius
COPY ./propius/load_balancer /propius/load_balancer
COPY ./propius/channels /propius/channels
COPY ./propius/util /propius/util
COPY ./propius/global_config.yml /propius/global_config.yml
COPY ./propius/requirements.txt /propius/requirements.txt

RUN pip3 install -r /propius/requirements.txt

CMD ["python", "./propius/load_balancer/load_balancer.py"]