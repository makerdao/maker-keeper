FROM python:3.6.6

RUN groupadd -r maker && useradd --no-log-init -r -g maker maker

COPY bin /opt/maker/autoline-keeper/bin
COPY lib /opt/maker/autoline-keeper/lib
COPY autoline_keeper /opt/maker/autoline-keeper/autoline_keeper
COPY install.sh /opt/maker/autoline-keeper/install.sh
COPY requirements.txt /opt/maker/autoline-keeper/requirements.txt

WORKDIR /opt/maker/autoline-keeper
RUN pip3 install virtualenv
RUN ./install.sh
WORKDIR /opt/maker/autoline-keeper/bin

USER maker
