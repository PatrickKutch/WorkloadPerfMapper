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
import json

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
    return int(round(time.time() )) # Gives you float secs since epoch

def GetCurrUS():
    return int(round(time.time() *100000)) # Gives you float secs since epoch, so make it us and chop



def calculateFibinacci(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculateFibinacci(n-1) + calculateFibinacci(n-2)

class GenericService(myRPC.SampleServiceServicer):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting grp service")

    def GenerateHash(self, request, context):
        
        startTime = GetCurrUS()

        response = myMessages.ServiceResponse()
        response.ServiceName = "Hash"

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

        if request.InputLen < 1:
            context.set_details("Hash input lenght of :  {0} not supported.".format(request.InputLen))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return response


        # Create a random string of length specified to have the hash generated on
        dataBuffer = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(request.InputLen))
        dataBuffer = dataBuffer.encode('utf-8')
        hash.update(dataBuffer)

        response.ResponseData = str(hash.digest())
        response.ProcessingTime = GetCurrUS() - startTime

        return response

    def PerformFibinacci(self, request, context):
        startTime = GetCurrUS()
        response = myMessages.ServiceResponse()
        response.ServiceName = "Fibinacci"
        if request.number < 0:
            context.set_details("Fibinacci requires a postive value: {0} is illegal.".format(request.Type))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return response

        response.ResponseData = str(calculateFibinacci(request.number))
        response.ProcessingTime = GetCurrUS() - startTime

        return response

    def PerformNoOp(self, request, context):
        response = myMessages.ServiceResponse()
        response.ServiceName = "NOOP"
        response.ProcessingTime = 0
        response.ResponseData = "noop"

        return response
        
    def PerformEtcd(self, request, context):
        startTime = GetCurrUS()
        response = myMessages.ServiceResponse()
        response.ServiceName = "ETCd"
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
        logger.info(str(response))
        return response

def handleNoOpRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing NOOP request")
    request = myMessages.Empty()   

    with grpc.insecure_channel(FIBINACCI_SERVICE) as channel:
        rpcStub = myRPC.SampleServiceStub(channel)
        response = rpcStub.PerformNoOp(request)
        logger.info(str(response))
        return response

def handleFibinacciRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing fibinacci request")
    request = myMessages.FibanacciRequest()   
    request.number = requestMap['size']

    with grpc.insecure_channel(FIBINACCI_SERVICE) as channel:
        rpcStub = myRPC.SampleServiceStub(channel)
        response = rpcStub.PerformFibinacci(request)
        logger.info(str(response))
        return response

def handleEtcdRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing etcd request")
    request = myMessages.EtcdRequest()   
    request.putCount= requestMap['put']
    request.getCount= requestMap['get']

    with grpc.insecure_channel(ETCD_SERVICE) as channel:
        rpcStub = myRPC.SampleServiceStub(channel)
        response = rpcStub.PerformEtcd(request)
        logger.info(str(response))
        return response
    
@app.route('/postjson',methods = ['POST'])
def postJsonHandler():
    global invalidRequests,requestsReceived,processedCount
    logger = logging.getLogger(__name__)

    startTimestamp = GetCurrUS()
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

    responseList=[]
    for service in content['services']:
        try:
            if service['service'].lower() == "hash":
                responseList.append(handleHashRequest(service))

            elif service['service'].lower() == "noop":
                responseList.append(handleNoOpRequest(service))

            elif service['service'].lower() == "fibinacci":
                responseList.append(handleFibinacciRequest(service))

            elif service['service'].lower() == "etcd":
                responseList.append(handleEtcdRequest(service))

            else:
                invalidRequests += 1
                return 'Invalid JSON posted'

        except grpc.RpcError as ex:
            invalidRequests += 1

            return "{0} --> {1}".format(status_code.name,ex.details())

        except Exception:
            logger.error("Service {0} unavailable".format(service['service']))

    processTime = GetCurrUS() - startTimestamp 

    jsonResponse=[]
    for serviceResp in responseList:
        response = {}
        response['Service'] =serviceResp.ServiceName
        response['ProcessingTime'] = serviceResp.ProcessingTime
        response['Data'] = serviceResp.ResponseData
        jsonResponse.append(response)


    jsonResponse.append({'Processing Time':str(processTime)})
    respStr = json.dumps(jsonResponse)
    return respStr

    #return 'JSON posted - ' + str(processTime)


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