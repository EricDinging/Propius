ARG WORKER_IMAGE
ARG DEVICE

FROM $WORKER_IMAGE

RUN if [ "$DEVICE" = "gpu" ]; then \
        ENV DEBIAN_FRONTEND=noninteractive; \
        RUN apt-get update && \
            apt-get install -y python3 python3-pip; \
    fi

WORKDIR /
RUN mkdir evaluation

COPY ./evaluation/commons.py evaluation/commons.py
COPY ./evaluation/requirements.txt evaluation/requirements.txt
COPY ./evaluation/internal /evaluation/internal

RUN pip install --upgrade pip
RUN pip install -r evaluation/requirements.txt
CMD ["python", "evaluation/single_executor/executor.py"]