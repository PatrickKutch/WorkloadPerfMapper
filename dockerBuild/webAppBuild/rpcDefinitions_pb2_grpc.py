# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import rpcDefinitions_pb2 as rpcDefinitions__pb2


class SampleServiceStub(object):
  """Interface exported by our 'Services'
  """

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.GenerateHash = channel.unary_unary(
        '/inteledgecloud.SampleService/GenerateHash',
        request_serializer=rpcDefinitions__pb2.HashRequest.SerializeToString,
        response_deserializer=rpcDefinitions__pb2.ServiceResponse.FromString,
        )
    self.PerformFibinacci = channel.unary_unary(
        '/inteledgecloud.SampleService/PerformFibinacci',
        request_serializer=rpcDefinitions__pb2.FibanacciRequest.SerializeToString,
        response_deserializer=rpcDefinitions__pb2.ServiceResponse.FromString,
        )
    self.PerformNoOp = channel.unary_unary(
        '/inteledgecloud.SampleService/PerformNoOp',
        request_serializer=rpcDefinitions__pb2.Empty.SerializeToString,
        response_deserializer=rpcDefinitions__pb2.ServiceResponse.FromString,
        )
    self.PerformEtcd = channel.unary_unary(
        '/inteledgecloud.SampleService/PerformEtcd',
        request_serializer=rpcDefinitions__pb2.EtcdRequest.SerializeToString,
        response_deserializer=rpcDefinitions__pb2.ServiceResponse.FromString,
        )


class SampleServiceServicer(object):
  """Interface exported by our 'Services'
  """

  def GenerateHash(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def PerformFibinacci(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def PerformNoOp(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def PerformEtcd(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_SampleServiceServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'GenerateHash': grpc.unary_unary_rpc_method_handler(
          servicer.GenerateHash,
          request_deserializer=rpcDefinitions__pb2.HashRequest.FromString,
          response_serializer=rpcDefinitions__pb2.ServiceResponse.SerializeToString,
      ),
      'PerformFibinacci': grpc.unary_unary_rpc_method_handler(
          servicer.PerformFibinacci,
          request_deserializer=rpcDefinitions__pb2.FibanacciRequest.FromString,
          response_serializer=rpcDefinitions__pb2.ServiceResponse.SerializeToString,
      ),
      'PerformNoOp': grpc.unary_unary_rpc_method_handler(
          servicer.PerformNoOp,
          request_deserializer=rpcDefinitions__pb2.Empty.FromString,
          response_serializer=rpcDefinitions__pb2.ServiceResponse.SerializeToString,
      ),
      'PerformEtcd': grpc.unary_unary_rpc_method_handler(
          servicer.PerformEtcd,
          request_deserializer=rpcDefinitions__pb2.EtcdRequest.FromString,
          response_serializer=rpcDefinitions__pb2.ServiceResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'inteledgecloud.SampleService', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
