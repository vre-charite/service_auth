FROM 10.32.42.225:5000/python:3.7-buster
USER root
RUN http_proxy="http://proxy.charite.de:8080/" apt-get update
RUN http_proxy="http://proxy.charite.de:8080/" apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev -y
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt --proxy="http://proxy.charite.de:8080/"
COPY . .
CMD ["./gunicorn_starter.sh"]
# CMD ["python","app.py"]
