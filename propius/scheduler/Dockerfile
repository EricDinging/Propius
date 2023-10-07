FROM python:3.9

WORKDIR /
RUN mkdir propius

COPY ./propius/channels propius/channels
COPY ./propius/util propius/util
COPY ./propius/database /propius/database

COPY ./propius/requirements.txt propius/requirements.txt
COPY ./setup.py /setup.py

RUN pip3 install -r propius/requirements.txt

RUN PROPIUS_HOME=$(pwd)
RUN echo export PROPIUS_HOME=$(pwd) >> ~/.bashrc
RUN . ~/.bashrc
RUN pip install -e .

CMD ["python", "-m", "propius.scheduler"]