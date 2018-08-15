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

    try:
        respData = json.loads(response.read().decode(response.info().get_param('charset') or 'utf-8'))

    except Exception as Ex:
        print("Error: " + str(Ex))

    if 'Error' in respData:
        print("Error: " + respData['Error'])

    else:
        overallDataMap = respData['Web-App-Info']
        tDelta = GetCurrUS() - float(overallDataMap['client-start-timestamp']) 

        clientInfo = {}
        clientInfo["Total-Time-us"] = "{0:.0f}".format(tDelta)
        clientInfo["Total-Time-ms"] = "{0:.0f}".format(tDelta/1000)
        rtt = tDelta - float(overallDataMap['Application-Processing-Time-us'])
        clientInfo["RTT-us"] = "{0:.0f}".format(rtt)
        clientInfo["RTT-ms"] = "{0:.0f}".format(rtt/1000)

        # Nuke data to display, depending on desired display verbosity
        if detailLevel < 3:
            overallDataMap.pop('Services-Called',None)
            for entry in respData['Services']:
                if 'RequestParemeters' in entry:
                    entry.pop('RequestParemeters',None)
                    entry.pop('Response-Data',None)

        if detailLevel < 2:
            for entry in respData['Services']:
                if 'ProcessingTime' in entry:
                    entry.pop('ProcessingTime',None)

        if detailLevel < 1:
            overallDataMap={}
            respData={}
#            respData['web-app-info'] = overallDataMap

        if detailLevel < 0:
            return

        respData["client"] = clientInfo 

        overallDataMap.pop('client-start-timestamp',None)


        ShowResponse(respData)

def PostRestMessage(targteServer,dataPkt,detailsLevel,repeatCount):
    for loop in range(0,repeatCount):
        PostData(targteServer,dataPkt,detailsLevel)


def main():
    parser = argparse.ArgumentParser(description='Micro-Services Simulator client.')

    parser.add_argument("targets", help="services to run and their parameters. Ex: hash{type=md5, length=322}, fibinacci{size=25}",nargs="*") #  hash{type=md5, length=322}, fibinacci{size=25}
    parser.add_argument("-s", "--server",help="where to connect to", type=str, required=True)
    parser.add_argument("-v", "--verbose",help="prints information, values 0-3",type=int)
    parser.add_argument("-m", "--multithread", help="number of threads to run",type=int,default=1)
    parser.add_argument("-c", "--count", help="number of times to send the request per thread", type=int,default=1)
    parser.add_argument("-o", "--output", help="output format (json|text)",type=str,default='json')

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

    if args.multithread < 1:
        logger.error("multithread option must be > 0")
        return

    if args.count < 1:
        logger.error("count option must be > 0")
        return


    targetList = []
    dataPktRaw = {}
    if len(args.targets) > 0:
        for target in args.targets:
            service={}
            if '{' in target:
                if '}' not in target:
                    logger.error("Malformed target: {0}".format(target))
                    return
                paramList=target.split("{")
                serviceName = paramList[0].strip().upper()
                service['Service'] = serviceName
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

    dataPktRaw['Services'] = targetList

    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        for loop in range(1,args.multithread-1):
            retData = executor.submit(PostRestMessage,args.server,dataPktRaw,-1,args.count)

        retData = executor.submit(PostRestMessage,args.server,dataPktRaw,_DetailLevel,args.count)

    

if __name__ == "__main__":
    main()
