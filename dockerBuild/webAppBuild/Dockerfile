# Use an official Python runtime as a parent image
FROM python:3.6-slim
# Disables buffered output - for logging
ENV PYTHONUNBUFFERD=0

RUN mkdir WorkloadPerfMan && \
pip install grpcio-tools googleapis-common-protos flask prometheus_client 
COPY *.proto *.py WorkloadPerfMan/


WORKDIR WorkloadPerfMan
RUN python run_codegen.py

# need the goodies for flask and Google RPC

ENTRYPOINT  ["python", "webApp.py"]

