FROM python:3.10.1

ADD ./requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

ADD ./src /app
WORKDIR /app

EXPOSE 8000
