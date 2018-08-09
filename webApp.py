##############################################################################
#  Copyright (c) 2018 Intel Corporation
# 
# Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
##############################################################################
#    File Abstract: 
#    This is the main/entry point file for the Minion data collector program
#
##############################################################################

import argparse
import logging
import grpc
from concurrent import futures
from flask import Flask
from flask import request
import sys
import time
import rpcDefinitions_pb2 as myMessages
import rpcDefinitions_pb2_grpc as myRPC
import hashlib
import string
import random

FIBINACCI_SERVICE="localhost:50001"
HASH_SERVICE="localhost:50001"
NOOP_SERVICE="localhost:50001"
ETCD_SERVICE="localhost:50001"

processedCount=0
requestsReceived=0
invalidRequests=0
starttime = 0

app = Flask(__name__)


def GetCurrentTime():
    return  int(round(time.time() )) # Gives you float secs since epoch

def GetCurrUS():
    return  int(round(time.time() *100000)) # Gives you float secs since epoch, so make it us and chop


def NoOp(params):
    return str("NoOp")
    

def RandHash(size):
    size = int(size)
    hash = hashlib.sha256()
    
    dataBuffer = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size))
    dataBuffer = dataBuffer.encode('utf-8')
    hash.update(dataBuffer)

    return str(hash.digest())

def Fib(params):
    return str(realFib(int(params[0])))

def realFib(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return realFib(n-1) + realFib(n-2)

class GenericService(myRPC.SampleServiceServicer):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting grp service")

    def GenerateHash(self, request, context):
        
        startTime = GetCurrUS()

        response = myMessages.ServiceResponse()

        hashStr = request.Type.lower()
        if hashStr == "sha256":
            hash = hashlib.sha256()

        elif hashStr == "sha1":
            hash = hashlib.sha1()

        elif hashStr == "md5":
            hash = hashlib.md5()

        else:
            context.set_details("Hash type:  {0} not supported.".format(request.Type))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return response

        response.ProcessingTime = GetCurrUS() - startTime
        response.ResponseData = RandHash(request.InputLen)

        return response

    def PerformFibinacci(self, request, context):
        startTime = GetCurrUS()
        response = myMessages.ServiceResponse()
        response.ProcessingTime = GetCurrUS() - startTime
        response.ResponseData = "Fibinacci"

        return response

    def PerformNoOp(self, request, context):
        response = myMessages.ServiceResponse()
        response.ProcessingTime = 0
        response.ResponseData = "noop"

        return response
        
    def PerformEtcd(self, request, context):
        startTime = GetCurrUS()
        response = myMessages.ServiceResponse()
        response.ProcessingTime = GetCurrUS() - startTime
        response.ResponseData = "etcd"

        return response

def runAsService():
    logger = logging.getLogger(__name__)
    logger.info("launching as service")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    myRPC.add_SampleServiceServicer_to_server(GenericService(),server)
    server.add_insecure_port('[::]:50001')
    server.start()

    try:
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        server.stop(0)
    
def runAsApp():
    app.run()

def handleHashRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing hash request")
    request = myMessages.HashRequest()   
    request.Type = requestMap['type']
    request.InputLen = requestMap['length']

    with grpc.insecure_channel(HASH_SERVICE) as channel:
        rpcStub = myRPC.SampleServiceStub(channel)
        response = rpcStub.GenerateHash(request)
        logger.info("Response from gRPC Hash call:")
        logger.info(str(response))

def handleNoOpRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing NOOP request")

def handleFibinacciRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing fibinacci request")

def handleEtcdRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing etcd request")

@app.route('/postjson',methods = ['POST'])
def postJsonHandler():
    global invalidRequests,requestsReceived,processedCount
    logger = logging.getLogger(__name__)

    requestsReceived += 1

    if not request.is_json:
        invalidRequests += 1
        return 'Invalid JSON posted'

    content = request.get_json()

    if not 'start-timestamp' in content:
        invalidRequests += 1
        return 'Invalid JSON posted'

    if not 'services' in content:
        invalidRequests += 1
        return 'Invalid JSON posted'

    if 'start-timestamp' in content:
        requeststartTime = content['start-timestamp']

    for service in content['services']:
        try:
            if service['service'].lower() == "hash":
                handleHashRequest(service)

            elif service['service'].lower() == "noop":
                handleNoOpRequest(service)

            elif service['service'].lower() == "fibinacci":
                handleFibinacciRequest(service)

            elif service['service'].lower() == "etcd":
                handleEtcdRequest(service)

            else:
                invalidRequests += 1
                return 'Invalid JSON posted'

        except grpc.RpcError as ex:
            from pprint import pprint as pprint
            #ex.details()
            status_code = ex.code()
            #status_code.name
            #status_code.value
            pprint(ex.details())
            return "{0} --> {1}".format(status_code.name,ex.details())

        except Exception:
            logger.error("Service {0} unavailable".format(service['service']))

    return 'JSON posted'


@app.route("/statistics")
def statistics():
    global starttime,invalidRequests,requestsReceived,processedCount
    seconds = round(GetCurrentTime() - starttime)
    strTime = ''
    for scale in 86400, 3600, 60:
        result, seconds = divmod(seconds, scale)
        result = (int)(result)
        seconds = (int) (seconds)
        if strTime != '' or result > 0:
            strTime += '{0:02d}:'.format(result)
    strTime += '{0:02d}'.format(seconds)

    return "Runtime: {0} request received: {1} invalid requests: {2}".format(strTime,requestsReceived,invalidRequests)


def main():
    global starttime
    starttime = GetCurrentTime()


    parser = argparse.ArgumentParser(description='Patrick\'s test app ')
    parser.add_argument("-r","--role",help="app, service",type=str,required=True)

    parser.add_argument("-v","--verbose",help="prints information, values 0-3",type=int)
    try:
        args = parser.parse_args()
        if None == args.verbose:
            _VerboseLevel = 0
        else:
            _VerboseLevel = args.verbose

    except:
        return

    if 3 <= _VerboseLevel:
        _VerboseLevel = logging.DEBUG

    elif 2 == _VerboseLevel:
        _VerboseLevel = logging.INFO

    elif 1 == _VerboseLevel:
        _VerboseLevel = logging.WARNING

    else:
        _VerboseLevel = logging.ERROR

    logging.basicConfig(level=_VerboseLevel,format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M')
    logger = logging.getLogger(__name__)

    if args.role.lower() == 'app':
        runAsApp()

    else:
        runAsService()

    

 
if __name__ == "__main__":
    main()
# [ {"service":"hash", "type":"md5","length":"32"},{"service":"noop"},{"service":"fib","size":"32"} ]

#{ "menu": [ { "description": "Spaghetti", "price": 7.99 }, { "description": "Steak", "price": 12.99 }, { "description": "Salad", "price": 5.99 } ], "name": "Future Studio Steak House" }

{
  "start-timestamp":"323892389238923",

 
  "services" :
  [
  	{ "service" : "hash", "type" : "md5", "length" : 32 },
  	{ "service" : "noop"},
  	{ "service" : "fibinacci", "size": 12},
  	{ "service" : "etcd", "put": 12, "get":4},
  	{ "service" : "fibinacci", "size": 32}
  ]


}