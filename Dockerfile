FROM python:3.9-slim

WORKDIR app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN apt-get update && apt-get install -y wget

ENV GECKODRIVER_VERSION 0.32.2
#RUN wget https://github.com/mozilla/geckodriver/releases/download/v$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz | tar -xz -C /usr/local/bin
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.32.2/geckodriver-v0.32.2-linux64.tar.gz | tar -xz -C /usr/local/bin

COPY . . 

CMD [ "python3", "-h"]
