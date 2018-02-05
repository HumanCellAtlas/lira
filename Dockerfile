FROM ubuntu:16.04

RUN apt-get update && apt-get upgrade -y && \
  apt-get -y install --no-install-recommends \
  python-pip \
  python-setuptools \
  vim \
  nmap \
  git

RUN pip install --upgrade pip

RUN pip install wheel

RUN mkdir /secondary-analysis
WORKDIR /secondary-analysis

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["bash", "start_lira.sh"]
