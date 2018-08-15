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
from concurrent import futures
import sys
import time
import json
import urllib.request
import urllib.error
from pprint import pprint as pprint
import time

ShowResponse = None

def GetCurrUS():
    return int(round(time.time() *1000000)) # Gives you float secs since epoch, so make it us and chop


def ShowResponseJSON(responseData):
    print(json.dumps(responseData,indent=4, sort_keys=True))

def PostData(where,what,detailLevel):
    # is a web service, so needs a web type address
    if not 'http://' in where.lower() and not 'https://' in where.lower():
        connectPoint = "http://" + where
    else:
        connectPoint = where

    myurl = connectPoint + "/performServices"
    req = urllib.request.Request(myurl)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    timestr = str(GetCurrUS())
    what["start-timestamp"] = timestr
    jsondata = json.dumps(what)
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))

    try:
        response = urllib.request.urlopen(req, jsondataasbytes)

    except urllib.error.URLError as Ex:
        logger = logging.getLogger(__name__)
        logger.error("Unable to connect to " + where)
        return

    except Exception as Ex:
        logger = logging.getLogger(__name__)
        logger.error(str(Ex))
        return

    respData = json.loads(response.read().decode(response.info().get_param('charset') or 'utf-8'))

    if 'Error' in respData:
        print("Error: " + respData['Error'])
    else:
        overallDataMap = respData[0]
        tDelta = GetCurrUS() - float(overallDataMap['client-start-timestamp']) 
        # Nuke data to display, depending on desired display verbosity
        if detailLevel < 3:
            overallDataMap.pop('client-start-timestamp',None)
            overallDataMap.pop('services-called',None)
            for entry in respData:
                if 'RequestParemeters' in entry:
                    entry.pop('RequestParemeters',None)
                    entry.pop('Data',None)

        if detailLevel < 2:
            for entry in respData:
                if 'ProcessingTime' in entry:
                    entry.pop('ProcessingTime',None)

        if detailLevel < 1:
            overallDataMap={}
            respData=[overallDataMap]

        overallDataMap["total-time-us"] = "{0:.0f}".format(tDelta)
        overallDataMap["total-time-ms"] = "{0:.0f}".format(tDelta/1000)

        ShowResponse(respData)

def main():
    parser = argparse.ArgumentParser(description='Micro-Services Simulator.')

    parser.add_argument("targets", help="services to run and their parameters. Ex: hash{type=md5, length=322}, fibinacci{size=25}",nargs="*") #  hash{type=md5, length=322}, fibinacci{size=25}
    parser.add_argument("-s", "--server",help="where to connect to", type=str, required=True)
    parser.add_argument("-v", "--verbose",help="prints information, values 0-3",type=int)

    try:
        args = parser.parse_args()
        if None == args.verbose:
            _VerboseLevel = 0
            _DetailLevel = 0
        else:
            _VerboseLevel = args.verbose


    except:
        return

    if 3 <= _VerboseLevel:
        _VerboseLevel = logging.DEBUG
        _DetailLevel = 3

    elif 2 == _VerboseLevel:
        _VerboseLevel = logging.INFO
        _DetailLevel = 2

    elif 1 == _VerboseLevel:
        _VerboseLevel = logging.WARNING
        _DetailLevel = 1

    else:
        _VerboseLevel = logging.ERROR
        _DetailLevel = 0

    logging.basicConfig(level=_VerboseLevel,format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M')
    logger = logging.getLogger(__name__)

    global ShowResponse
    ShowResponse = ShowResponseJSON

    multiThreaded = False
    targetList = []
    dataPktRaw = {}
    if len(args.targets) > 0:
        multiThreaded = False
        for target in args.targets:
            service={}
            if '{' in target:
                if '}' not in target:
                    logger.error("Malformed target: {0}".format(target))
                    return
                paramList=target.split("{")
                serviceName = paramList[0].strip().upper()
                service['service'] = serviceName
                paramList = paramList[1].split('}')
                if ',' in paramList[0]:
                    paramList=paramList[0].split(',')
                
                for param in paramList:
                    param = param.strip()
                    if len(param) < 3:
                        continue
                    key,value = param.split('=')
                    key = key.strip()
                    value=value.strip()
                    service[key] = value

            targetList.append(service)

    else:
        logger.error("No targets specified.")
        return

    dataPktRaw['services'] = targetList

    PostData(args.server,dataPktRaw,_DetailLevel)
    

if __name__ == "__main__":
    main()
