FROM python:3.9

WORKDIR /
COPY ./propius/scheduler /propius/scheduler
COPY ./propius/channels /propius/channels
COPY ./propius/util /propius/util
COPY ./propius/global_config.yml /propius/global_config.yml
COPY ./propius/requirements.txt /propius/requirements.txt

RUN pip3 install -r /propius/requirements.txt

CMD ["python", "./propius/scheduler/scheduler.py"]