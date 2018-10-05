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
import rpcDefinitions_pb2 as myMessages # Simplified usage
import rpcDefinitions_pb2_grpc as myRPC
import hashlib
import string
import random
import json
import os
from prometheus_client import start_http_server, Summary

# Some globals used for stats
processedCount=0
requestsReceived=0
invalidRequests=0
starttime = 0

VersionStr="18.10.05 Build 2"

# for Flask object when this is run as the web application
app = Flask(__name__)

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

def GetCurrentTime():
    return int(round(time.time() )) # Gives you float secs since epoch

def GetCurrUS():
    return int(round(time.time() *1000000)) # Gives you float secs since epoch, so make it us and chop

# --------------- Begin routines for the 'Service' workers ----------------------
def calculateFibinacci(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculateFibinacci(n-1) + calculateFibinacci(n-2)

def getServiceEndpoint(serviceName):
    if 'SERVICE_DISCOVERY_DIR' in os.environ.keys():
        fName = os.environ['SERVICE_DISCOVERY_DIR'] + serviceName
        logger = logging.getLogger(__name__)
        logger.debug("Service: {0} is at in file {1}".format(serviceName,fName))
        try:
            with open(fName, "rt") as inpFile:
                endpoint = inpFile.read().strip()
                logger.debug("Service: {0} is at {1}".format(serviceName,endpoint))
                return endpoint
                
        except FileNotFoundError:
            raise FileNotFoundError("Service Endpoint definition file {0} is not found".format(fName))

    else:
        logger = logging.getLogger(__name__)
        logger.error("Environment variable SERVICE_DISCOVERY_DIR not set")
        return "Environment variable SERVICE_DISCOVERY_DIR not set"


class ResponseWrapper():
    def __init__(self,howLong, what):
        self.rpcTime = howLong
        self.response = what

class GenericService(myRPC.SampleServiceServicer):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hashCounter = 0
        self.noopCounter = 0
        self.etcdCounter = 0
        self.fibinacciCounter = 0

    @REQUEST_TIME.time()
    def GenerateHash(self, request, context):
        startTime = GetCurrUS()

        response = myMessages.ServiceResponse()
        response.ServiceName = "HASH"

        requestParam = response.RequestParameter.add()
        requestParam.Key = 'type'
        requestParam.Value = request.Type

        requestParam = response.RequestParameter.add()
        requestParam.Key = 'length'
        requestParam.Value = str(request.InputLen)

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
        self.hashCounter += 1
        response.CalledCounter = self.hashCounter

        response.ProcessingTime = GetCurrUS() - startTime

        return response

    @REQUEST_TIME.time()
    def PerformFibinacci(self, request, context):
        startTime = GetCurrUS()
        response = myMessages.ServiceResponse()
        response.ServiceName = "FIBINACCI"

        requestParam = response.RequestParameter.add()
        requestParam.Key = 'size'
        requestParam.Value = str(request.number)

        if request.number < 0:
            context.set_details("Fibinacci requires a postive value: {0} is illegal.".format(request.Type))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return response

        response.ResponseData = str(calculateFibinacci(request.number))
        self.fibinacciCounter += 1
        response.CalledCounter = self.fibinacciCounter

        response.ProcessingTime = GetCurrUS() - startTime

        return response

    @REQUEST_TIME.time()
    def PerformNoOp(self, request, context):
        response = myMessages.ServiceResponse()
        response.ServiceName = "NOOP"
        response.ProcessingTime = 0
        response.ResponseData = "NOOP Response Data"
        self.noopCounter += 1
        response.CalledCounter = self.noopCounter

        return response
        
    @REQUEST_TIME.time()
    def PerformEtcd(self, request, context):
        startTime = GetCurrUS()
        response = myMessages.ServiceResponse()
        response.ServiceName = "ETCD"

        response.ProcessingTime = GetCurrUS() - startTime
        response.ResponseData = "etcd"
        self.etcdCounter += 1
        response.CalledCounter = self.etcdCounter

        return response

def runAsService(hostAddr,hostPort):
    logger = logging.getLogger(__name__)
    print("Launching as service at {0}:{1}. Version: {2}".format(hostAddr,hostPort,VersionStr))

    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        myRPC.add_SampleServiceServicer_to_server(GenericService(),server)
    except Exception as Ex:
        logger.error("Error Starting server:")
        logger.error(str(Ex))
        return
    
    try:
        server.add_insecure_port(hostAddr +':' + str(hostPort))
        server.start()
        logger.debug("Service Started")
    except Exception as Ex:
        logger.error("Error Starting Service:")
        logger.error(str(Ex))
        return

    # server returns, so let's just spin for a while
    try:
        while True:
            time.sleep(1000)

    except KeyboardInterrupt:
        server.stop(0)

# --------------- End routines for the 'Service' workers ----------------------
    
# --------------- Begin routines for the 'web app' ----------------------
def runAsApp(hostAddr,hostPort):
    logger = logging.getLogger(__name__)
    print("Starting Web Service Application at {0}:{1}.  Version: {2}".format(hostAddr,hostPort,VersionStr))

    if not 'SERVICE_DISCOVERY_DIR' in os.environ:
        logger.warning("SERVICE_DISCOVERY_DIR environment variable not set.  Will search for config files in /var/workloadmapper/ .")
        os.environ['SERVICE_DISCOVERY_DIR'] = '/var/workloadmapper/'

    try:
        app.run(host=hostAddr,port=hostPort)
        
    except Exception as Ex:
        logger.error(str(Ex) + " -> {0}:{1}".format(hostAddr,hostPort))

def handleHashRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing hash request")
    request = myMessages.HashRequest()

    if not 'type' in requestMap:
        raise ValueError("Hash type not specified")
    if not 'length' in requestMap:
        raise ValueError("Hash length not specified")

    request.Type = requestMap['type']
    try:
        request.InputLen = int(requestMap['length'])
    except ValueError:
        raise ValueError("Invalid Hash length specified")

    with grpc.insecure_channel(getServiceEndpoint("HASH_SERVICE_ENDPOINT")) as channel:
        rpcStub = myRPC.SampleServiceStub(channel)
        response = rpcStub.GenerateHash(request)
        logger.info(str(response))
        return response

def handleNoOpRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing NOOP request, endpoint: " + getServiceEndpoint("NOOP_SERVICE_ENDPOINT"))
    request = myMessages.Empty()   

    with grpc.insecure_channel(getServiceEndpoint("NOOP_SERVICE_ENDPOINT")) as channel:
        rpcStub = myRPC.SampleServiceStub(channel)
        response = rpcStub.PerformNoOp(request)
        logger.info(str(response))
        return response

def handleFibinacciRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing fibinacci request")
    request = myMessages.FibanacciRequest()   

    if not 'size' in requestMap:
        raise ValueError("Fibinacci size not specified")

    try:
        request.number = int(requestMap['size'])
    except ValueError:
        raise ValueError("Invalid Fibinacci size specified")

    with grpc.insecure_channel(getServiceEndpoint("FIBINACCI_SERVICE_ENDPOINT")) as channel:
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

    with grpc.insecure_channel(getServiceEndpoint("ETCD_SERVICE_ENDPOINT")) as channel:
        rpcStub = myRPC.SampleServiceStub(channel)
        response = rpcStub.PerformEtcd(request)
        logger.info(str(response))
        return response
    
@app.route('/performServices',methods = ['POST'])
def performServicesHandler():
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

    if not 'Services' in content:
        invalidRequests += 1
        return 'Invalid JSON posted'

    if 'start-timestamp' in content:
        requeststartTime = content['start-timestamp']

    responseList=[]
    for service in content['Services']:
        try:
            svcName = "Malformed request - Service not found in map"

            svcName = service['Service']

            startServiceTimestamp = GetCurrUS()

            if svcName == "HASH":
                response = handleHashRequest(service)

            elif svcName == "NOOP":
                response = handleNoOpRequest(service)

            elif svcName == "FIBINACCI":
                response = handleFibinacciRequest(service)

            elif svcName == "ETCD":
                response = handleEtcdRequest(service)

            else:
                invalidRequests += 1
                return 'Invalid JSON posted'

            # gRPC object is immutable, so throw in a wrapper along with how long RPC call took
            wrapper = ResponseWrapper(GetCurrUS() - startServiceTimestamp,response)
            responseList.append(wrapper)

        except grpc.RpcError as ex:
            invalidRequests += 1
            status_code = ex.code()
            logger.error ("{0} --> {1}".format(status_code.name,ex.details()))
            return json.dumps({"Error" : ex.details() })

        except ValueError as Ex:
            logger.error("Invalid Parameter: " + str(service))
            return json.dumps({"Error" : "Invalid Parameter: " + str(Ex) })

        except Exception as Ex:
            logger.error("Service {0} unavailable: {1}".format(svcName, str(Ex)))
            return json.dumps({"Error" : "Service HASH unavailable"})

    processTime = GetCurrUS() - startTimestamp 

    jsonResponse={}
    jsonResponse['Services'] = []
    for serviceResp in responseList:
        response = {}
        responseObj = serviceResp.response

        response['Service'] = responseObj.ServiceName
        response['RPC Time'] = serviceResp.rpcTime
        response['Network RTT'] = int(serviceResp.rpcTime) - (responseObj.ProcessingTime)
        response['ProcessingTime'] = responseObj.ProcessingTime
        response['Response-Data'] = responseObj.ResponseData
        response['RequestParemeters'] = []
        for Param in responseObj.RequestParameter:
            response['RequestParemeters'].append({Param.Key : Param.Value})

        response['Processed-Count'] = responseObj.CalledCounter

        jsonResponse['Services'].append(response)

    processedCount += 1
    overallDataMap={}
    overallDataMap['Processed-Count'] = str(processedCount)
    overallDataMap['Application-Processing-Time-us'] = str(processTime)
    overallDataMap['Application-Processing-Time-ms'] = "{0:.0f}".format(processTime/1000)
    overallDataMap['client-start-timestamp'] = requeststartTime
    overallDataMap['Services-Called'] = str(len(responseList))

    jsonResponse['Web-App-Info'] = overallDataMap
    
    respStr = json.dumps(jsonResponse)
    return respStr

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

# --------------- end routines for the 'web app' ----------------------


def main():
    global starttime
    starttime = GetCurrentTime()

    parser = argparse.ArgumentParser(description='Patrick\'s test app ')
    parser.add_argument("-r","--role",help="app | service",type=str,required=True)
    parser.add_argument("-v","--verbose",help="prints information, values 0-3",type=int)
    parser.add_argument("-c","--connect",help="ip:port to listen on.",type=str,required=True)

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

    if not ":" in args.connect:
        logger.error("Invalid connection information: " + args.connect)
        return

    parts = args.connect.split(':')
    if not len(parts) == 2:
        logger.error("Invalid connection information: " + args.connect)
        return
    ip = parts[0]
    try:
        port = int(parts[1])
    except Exception:
        logger.error("Invalid connection information: " + args.connect)
        return

    if args.role.lower() == 'app':
        runAsApp(ip,port)

    elif args.role.lower() == 'service':
        runAsService(ip,port)

    else:
        logger.error("Unsupported Role specified: " + args.role)

if __name__ == "__main__":
    main()
