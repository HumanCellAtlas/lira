FROM ubuntu:16.04

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get -y install software-properties-common && \
    apt-get -y install --no-install-recommends \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-wheel && \
    add-apt-repository ppa:certbot/certbot && \
    apt-get update && \
    apt-get -y install --no-install-recommends \
    vim \
    git \
    curl \
    jq \
    certbot && \
    pip3 install --upgrade pip

RUN pip3 install awscli --upgrade
