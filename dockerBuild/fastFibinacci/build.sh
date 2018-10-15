#/bin/sh

cp ../../*.py .

docker build --no-cache --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg HTTP_PROXY=$http_proxy --build-arg HTTPS_PROXY=$https_proxy --network=host -t patrickkutch/fastfibinacci .

docker push patrickkutch/fastfibinacci