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
from flask import Flask
from flask import request
from pprint import pprint as pprint
import sys
import time
processedCount=0
requestsReceived=0
invalidRequests=0
starttime = 0

app = Flask(__name__)


def __GetCurrentTime():
    return  int(round(time.time() )) # Gives you float secs since epoch


def NoOp(params):
    return str("NoOp")
    

def RandHash(params):
    import hashlib,random,string
    size = int(params[0])
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


def runAsApp():
    app.run()

def handleHashRequest(requestMap):
    logger = logging.getLogger(__name__)
    logger.info("Processing hash request")
    

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

    requestsReceived += 1

    if not request.is_json:
        invalidRequests += 1
        return 'Invalid JSON posted'

    content = request.get_json()
    pprint (content)

    if not 'start-timestamp' in content:
        invalidRequests += 1
        return 'Invalid JSON posted'

    if not 'services' in content:
        invalidRequests += 1
        return 'Invalid JSON posted'

    if 'start-timestamp' in content:
        requeststartTime = content['start-timestamp']

    for service in content['services']:
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


    return 'JSON posted'


@app.route("/statistics")
def statistics():
    global starttime,invalidRequests,requestsReceived,processedCount
    seconds = round(__GetCurrentTime() - starttime)
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
    starttime = __GetCurrentTime()


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
        logger.info("launching as service %s",args.role)
    

 
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