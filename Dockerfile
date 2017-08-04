FROM ubuntu:17.04

RUN apt-get update && apt-get upgrade -y

RUN apt-get -y install --no-install-recommends \
  python-pip \
  python-setuptools \
  vim \
  nmap

RUN mkdir /secondary-analysis
WORKDIR /secondary-analysis

COPY requirements.txt .

RUN pip install wheel && \
  pip install -r requirements.txt

RUN apt-get install -y lsb-release curl && \
  export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
  echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
  apt-get update && apt-get install -y google-cloud-sdk

COPY test_key.json .

RUN gcloud config set project broad-dsde-mint-dev && \
  gcloud auth activate-service-account --key-file=/secondary-analysis/test_key.json; exit 0

COPY . .

CMD ["python", "green-box-api"]
