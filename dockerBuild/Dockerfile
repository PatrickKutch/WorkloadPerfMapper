# Use an official Python runtime as a parent image
FROM python:3.6-slim
RUN mkdir WorkloadPerfMan
COPY *.py WorkloadPerfMan
WORKDIR WorkloadPerfMan
# need the goodies for flask and Google RPC
RUN pip install grpcio-tools googleapis-common-protos flask

