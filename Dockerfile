FROM python
RUN apt update && \
    apt install libsasl2-dev python-dev libldap2-dev libssl-dev && \
    apt clean

RUN curl https://bootstrap.pypa.io/pip/2.6/get-pip.py --output get-pip.py && \
    python2 get-pip.py

WORKDIR /app

COPY . .

RUN pip2 install requirements.txt

ENTRYPOINT ["python2 server.py"]

