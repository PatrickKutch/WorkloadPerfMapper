#/bin/sh

cp ../*.py .

docker build --network=host -t patrickkutch/workloadmapper . 
