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

RUN pip install google-cloud

COPY . .

RUN pip install -e 'green_box_tools/listener_utils'

CMD ["bash", "listener-start.sh"]
