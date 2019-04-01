FROM python:3.6

RUN pip install --upgrade \
        pip \
        setuptools \
        wheel && \
    mkdir /lira

WORKDIR /lira

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["bash", "start_lira.sh"]
