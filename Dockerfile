FROM ubuntu:17.04

RUN apt-get update && apt-get upgrade -y

RUN apt-get -y install --no-install-recommends \
  python-pip \
  python-setuptools \
  vim \
  nmap \
  git

RUN pip install wheel

RUN mkdir /secondary-analysis
WORKDIR /secondary-analysis

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "lira/lira.py"]
