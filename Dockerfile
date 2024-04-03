FROM python:3.9

RUN groupadd -r maker && useradd --no-log-init -r -g maker maker

COPY bin /opt/maker/maker-keeper/bin
ADD lib /opt/maker/maker-keeper/lib
COPY maker_keeper /opt/maker/maker-keeper/maker_keeper
COPY install.sh /opt/maker/maker-keeper/install.sh
COPY requirements.txt /opt/maker/maker-keeper/requirements.txt

WORKDIR /opt/maker/maker-keeper
RUN pip3 install virtualenv
RUN ./install.sh
WORKDIR /opt/maker/maker-keeper/bin

USER maker
