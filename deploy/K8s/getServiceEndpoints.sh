#!/bin/bash

# Go get all services where the web app is at 'edge' and put in files

#1st file is where the services are running on some node as the app
kubectl -n app-at-edge-ns get service --selector locale=applocal -o=jsonpath='{range .items[*]}{.metadata.name}{"="}{.spec.clusterIP}{":"}{.spec.ports[0].port}{"\n"}{end}' > app-at-edge-services-local.txt
#2nd file is where the services are not running on same node  as the app
kubectl -n app-at-edge-ns get service --selector locale=appremote -o=jsonpath='{range .items[*]}{.metadata.name}{"="}{.spec.clusterIP}{":"}{.spec.ports[0].port}{"\n"}{end}' > app-at-edge-services-remote.txt

kubectl -n app-at-edge-ns get service wpm-noop-applocal-service -o=jsonpath='{"NOOP_SERVICE_ENDPOINT="}{.spec.clusterIP}{":"}{.spec.ports[0].port}{"\n"}' > app-at-edge-configmap
kubectl -n app-at-edge-ns get service wpm-hash-applocal-service -o=jsonpath='{"HASH_SERVICE_ENDPOINT="}{.spec.clusterIP}{":"}{.spec.ports[0].port}{"\n"}' >> app-at-edge-configmap
kubectl -n app-at-edge-ns get service wpm-fibinacci-applocal-service -o=jsonpath='{"FIBINACCI_SERVICE_ENDPOINT="}{.spec.clusterIP}{":"}{.spec.ports[0].port}{"\n"}' >> app-at-edge-configmap

echo
echo
echo Services running on same node as web app [app-at-edge-services-local.txt]
cat app-at-edge-services-local.txt

echo 
echo 

echo Services running on different nods as web app [app-at-edge-services-remote.txt]
cat app-at-edge-services-remote.txt