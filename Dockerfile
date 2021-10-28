FROM python:3.7-buster
USER root
RUN apt-get update
RUN apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev -y
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["./gunicorn_starter.sh"]
# CMD ["python","app.py"]
