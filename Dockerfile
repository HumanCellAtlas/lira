FROM ubuntu:16.04

RUN apt-get update && apt-get upgrade -y && \
  apt-get -y install --no-install-recommends \
  python3-pip \
  vim \
  nmap \
  git

RUN pip3 install --upgrade pip setuptools

RUN pip3 install wheel

RUN mkdir /lira
WORKDIR /lira

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT ["bash", "start_lira.sh"]
