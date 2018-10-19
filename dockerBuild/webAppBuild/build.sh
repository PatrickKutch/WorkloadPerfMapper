#/bin/sh
rm *.py
rm *.proto
cp ../../*.py .
cp ../../*.proto .

docker build --no-cache --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg HTTP_PROXY=$http_proxy --build-arg HTTPS_PROXY=$https_proxy --network=host -t patrickkutch/workloadmapper .

docker push patrickkutch/workloadmapper
