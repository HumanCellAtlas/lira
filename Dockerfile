FROM ubuntu:17.04

RUN apt-get update && apt-get upgrade -y

RUN apt-get -y install --no-install-recommends \
  python-pip \
  python-setuptools \
  vim \
  nmap

RUN mkdir /secondary-analysis
WORKDIR /secondary-analysis

# pip doesn't preserve the order that we ask to install things when we give a big list and
# we need wheel before we can install anything else
RUN pip install wheel && \
    pip install connexion

COPY . .

RUN cd listener_utils && pip install .

CMD ["bash", "listener-start.sh"]
