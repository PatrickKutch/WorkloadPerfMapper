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
import sys
import time
import rpcDefinitions_pb2 as myMessages # Simplified usage
import rpcDefinitions_pb2_grpc as myRPC
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

VersionStr="18.10.15 Build 1"

cache=[]
# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

def GetCurrentTime():
    return int(round(time.time() )) # Gives you float secs since epoch

def GetCurrUS():
    return int(round(time.time() *1000000)) # Gives you float secs since epoch, so make it us and chop

# --------------- Begin routines for the 'Service' workers ----------------------
def calculateFibinacci(n):
   global cache
   if n == 1:
      return 1
   elif n == 0:   
      return 0 
   elif None != cache[n]:
      return cache[n]        
   else:   
      cache[n] = fib(n-1) + fib(n-2)                   
      return cache[n] 



class ResponseWrapper():
    def __init__(self,howLong, what):
        self.rpcTime = howLong
        self.response = what

class GenericService(myRPC.SampleServiceServicer):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fibinacciCounter = 0

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

def main():
    global starttime
    starttime = GetCurrentTime()

    parser = argparse.ArgumentParser(description='Patrick\'s test app ')
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
        
   runAsService(ip,port)


if __name__ == "__main__":
    main()
