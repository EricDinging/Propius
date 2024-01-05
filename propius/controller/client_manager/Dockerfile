FROM python:3.9

WORKDIR /
RUN mkdir propius
RUN mkdir propius/client_manager

COPY ./propius/requirements.txt propius/requirements.txt
COPY ./propius/client_manager/entrypoint.sh propius/client_manager/entrypoint.sh
COPY ./setup.py /setup.py

RUN pip3 install -r propius/requirements.txt
RUN chmod +x propius/client_manager/entrypoint.sh

RUN PROPIUS_HOME=$(pwd)
RUN echo export PROPIUS_HOME=$(pwd) >> ~/.bashrc
RUN . ~/.bashrc
RUN pip install -e .

ENTRYPOINT ["./propius/client_manager/entrypoint.sh"]