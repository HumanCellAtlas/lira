FROM ubuntu:17.04

RUN apt-get update && apt-get upgrade -y

RUN apt-get -y install --no-install-recommends \
  python-pip \
  python-setuptools \
  vim \
  nmap

RUN mkdir /secondary-analysis
WORKDIR /secondary-analysis

RUN pip install wheel

RUN pip install connexion

RUN apt-get install -y lsb-release curl && \
  export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
  echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
  apt-get update && apt-get install -y google-cloud-sdk

COPY . .

CMD ["bash", "listener-start.sh"]
