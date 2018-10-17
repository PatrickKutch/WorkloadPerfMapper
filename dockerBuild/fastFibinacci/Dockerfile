# Use an official Python runtime as a parent image
FROM python:3.6-slim
# Disables buffered output - for logging
ENV PYTHONUNBUFFERD=0

RUN mkdir WorkloadPerfMan && \
pip install grpcio-tools googleapis-common-protos prometheus_client
COPY fastFibinacci.py rpcDefinitions_pb2.py rpcDefinitions_pb2_grpc.py WorkloadPerfMan/


WORKDIR WorkloadPerfMan
# need the goodies for flask and Google RPC
#RUN pip install grpcio-tools googleapis-common-protos prometheus_client

ENTRYPOINT  ["python", "fastFibinacci.py"]

