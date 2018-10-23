# Use an official Python runtime as a parent image
FROM python:3.6-slim
# Disables buffered output - for logging
ENV PYTHONUNBUFFERD=0

RUN mkdir WorkloadPerfMan && \
pip install grpcio-tools googleapis-common-protos prometheus_client 

COPY fastFibonacci.py run_codegen.py *.proto WorkloadPerfMan/


WORKDIR WorkloadPerfMan
RUN python run_codegen.py

ENTRYPOINT  ["python", "fastFibonacci.py"]

