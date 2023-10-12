FROM python:3.9

WORKDIR /
RUN mkdir evaluation
RUN mkdir propius

COPY ./evaluation/requirements_peripheral.txt evaluation/requirements_peripheral.txt
COPY ./setup.py /setup.py

RUN pip install --upgrade pip
RUN pip install -r evaluation/requirements_peripheral.txt

RUN PROPIUS_HOME=$(pwd)
RUN echo export PROPIUS_HOME=$(pwd) >> ~/.bashrc
RUN . ~/.bashrc
RUN pip install -e .

ENTRYPOINT ["/evaluation/job/entrypoint.sh"]