FROM tiangolo/uwsgi-nginx-flask:python3.10
RUN apt update && apt dist-upgrade -y && apt install curl
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
