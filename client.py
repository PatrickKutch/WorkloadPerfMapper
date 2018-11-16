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
import argparse, textwrap
import logging
from concurrent import futures
import sys
import socket
import time
import json
import urllib.request
import urllib.error
from pprint import pprint as pprint
import time

ShowResponse = None
VersionStr="18.10.19 Build 1"
args = None

def GetCurrUS():
    return int(round(time.time() * 1000000.0)) # Gives you float secs since epoch, so make it us and chop

def GetCurrMS():
    return int(round(time.time() * 1000.0)) # Gives you float secs since epoch, so make it us and chop


def ShowResponseJSON(responseData):
    print(json.dumps(responseData,indent=4, sort_keys=True))
    
def MirrorToMinion(responseData):
    global args
    try:
      args.mirrorSocket.sendto(bytes(json.dumps(responseData,indent=4),'utf-8'),args.target)
    except Exception as Ex:
      print(str(Ex))

def PostData(where,what,detailLevel,mirrorFn):
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
        logger = logging.getLogger(__name__)
        logger.error("from remote:")
        logger.error(str(Ex))
        return

    if 'Error' in respData:
        print("Error: " + respData['Error'])

    else:
        # -1 is for multi-threaded, and we only need to print/provide data for a single one
        if detailLevel < 0:
            return

        overallDataMap = respData['Web-App-Info']
        tDelta = GetCurrUS() - float(overallDataMap['client-start-timestamp']) 

        clientInfo = {}
        clientInfo["TotalTime"] = "{0:.2f}".format(tDelta)
        clientInfo["TotalTime.ms"] = "{0:.2f}".format(tDelta/1000)
        rtt = tDelta - float(overallDataMap['Application-Processing-Time-us'])
        clientInfo["Time.RTT"] = "{0:.2f}".format(rtt)
        clientInfo["Time.RTT.ms"] = "{0:.2f}".format(rtt/1000)

        
        # Nuke data to display, depending on desired display verbosity
        if detailLevel < 3:
            overallDataMap.pop('Services-Called',None)
            for service in respData['Service']:
                svcMap = respData['Service'][service]
                if 'RequestParemeters' in svcMap:
                    svcMap.pop('RequestParemeters',None)
                    svcMap.pop('ResponseData',None)

        if detailLevel < 2:
            for service in respData['Service']:
                svcMap = respData['Service'][service]
                if 'ProcessingTime' in svcMap:
                    svcMap.pop('ProcessingTime',None)
                    
        # if detail is =, only show client info
        if detailLevel < 1:
            overallDataMap={}
            respData={}
        respData["client"] = clientInfo 

        overallDataMap.pop('client-start-timestamp',None)
        
        pprint(respData)
        # Go and create a ms entry from the us data
        if 'Service' in respData:
          for service in respData['Service']:
            svcMap = respData['Service'][service]
            respData['Service'][service]['Time.Processing.ms'] = "{0:.2f}".format(int(respData['Service'][service]['Time.Processing'])/1000)
            respData['Service'][service]['Time.RPC.ms'] = "{0:.2f}".format(int(respData['Service'][service]['Time.RPC'])/1000)
            respData['Service'][service]['Time.RTT.ms'] = "{0:.2f}".format(int(respData['Service'][service]['Time.RTT'])/1000)

        ShowResponse(respData)
        if None != mirrorFn:
            mirrorFn(respData)

def PostRestMessage(targteServer,dataPkt,detailsLevel,repeatCount,mirrorFn=None):
    for loop in range(0,repeatCount):
        PostData(targteServer,dataPkt,detailsLevel,mirrorFn)

def main():
    parser = argparse.ArgumentParser(description='Micro-Services Simulator client.',formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("targets", nargs="*", type=str,
                        help=textwrap.dedent('''\
                        services to run and their parameters the [] are required. 
                        Ex: hash[type=md5,length=322] fibonacci[size=25]
                        valid options:
                        hash[type=hashType,length=buffSize]
                            where 
                                hashType = md5 | sha1 | sha256
                                buffSize = size of random buffer to create and run has open
                        fibonacci[size=num]
                            where
                                size = how high to calculate fibonacci tuple_iterator
                        noop[] - does nothing but return'''))
                                    

    parser.add_argument("-s", "--server",help="where to connect to", type=str, required=True)
    parser.add_argument("-v", "--verbose",help="prints information, values 0-3",type=int,default=0)
    parser.add_argument("-t", "--multithread", help="number of threads to run",type=int,default=1)
    parser.add_argument("-c", "--count", help="number of times to send the request per thread", type=int,default=1)
    parser.add_argument("-m", "--mirror",help='specifies mirror target ip and port to send a copy of the incoming packets to',type=str)
    parser.add_argument("-o", "--output", help="output format (json|text)",type=str,default='json')

    try:
        global args
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
    
    if None != args.mirror:
      ip,port=args.mirror.split(":")
      port = int(port)
      args.target = (ip,port)
      args.mirrorSocket = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM) 
      
    else:
      args.mirrorSocket = None

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
            if '[' in target:
                if ']' not in target:
                    logger.error("Malformed target: {0}".format(target))
                    return
                paramList=target.split("[")
                serviceName = paramList[0].strip().upper()
                service['Service'] = serviceName
                paramList = paramList[1].split(']')
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
            else:
                logger.error("Invalid command line parameters. Every service must have [] list")
                return

            targetList.append(service)

    else:
        logger.error("No targets specified.")
        return

    dataPktRaw['Services'] = targetList
    
    logger.info("Attempting to connect to {0}".format(args.server))
    

    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        for loop in range(1,args.multithread-1):
            retData = executor.submit(PostRestMessage,args.server,dataPktRaw,-1,args.count,None)
            
        if None != args.mirrorSocket:
             sendFn = MirrorToMinion
        else:
             sendFn = None
             
        retData = executor.submit(PostRestMessage,args.server,dataPktRaw,_DetailLevel,args.count,sendFn)
    

if __name__ == "__main__":
    print("Tester Client Application.  Version: " + VersionStr)
    main()
