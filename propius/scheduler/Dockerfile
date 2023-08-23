FROM continuumio/anaconda3

COPY ./propius/ /propius/
COPY ./environment.yml /propius/environment.yml

RUN conda env create -f /propius/environment.yml


RUN echo "source activate propius" >> ~/.bashrc
ENV PATH /opt/conda/envs/propius/bin:$PATH

WORKDIR /

# CMD ["python", "./propius/scheduler/scheduler.py"]