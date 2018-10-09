# Use an official Python runtime as a parent image
FROM python:3.6-slim
# Disables buffered output - for logging
ENV PYTHONUNBUFFERD=0

RUN mkdir WorkloadPerfMan && \
pip install grpcio-tools googleapis-common-protos flask prometheus_client
COPY *.py WorkloadPerfMan/


WORKDIR WorkloadPerfMan
# need the goodies for flask and Google RPC
#RUN pip install grpcio-tools googleapis-common-protos flask prometheus_client

ENTRYPOINT  ["python", "webApp.py"]

