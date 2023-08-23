FROM python:3.9

WORKDIR /
RUN mkdir /propius
COPY ./propius/client_manager /propius/client_manager
COPY ./propius/channels /propius/channels
COPY ./propius/util /propius/util
COPY ./propius/global_config.yml /propius/global_config.yml
COPY ./propius/requirements.txt /propius/requirements.txt

RUN pip install --no-cache-dir -r /propius/requirements.txt

CMD ["python", "./propius/client_manager/client_manager.py", "0"]