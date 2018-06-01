FROM alpine
MAINTAINER Lily Mayfield <lily.m.mayfield@gmail.com>

# update!
RUN apk update

# basic flask environment
RUN apk add --no-cache bash git nginx uwsgi uwsgi-python3 redis \
    && pip3 install --upgrade pip \
    && pip3 install flask

RUN apk --update add --no-cache zlib-dev python3-dev \
    libxml2-dev libxslt-dev libffi-dev gcc musl-dev libgcc curl \
    alpine-sdk openssl-dev python-dev \
    #libxml2-dev libxslt-dev libffi-dev gcc musl-dev libgcc openssl-dev curl \
    zlib-dev freetype-dev lcms2-dev tiff-dev tk-dev tcl-dev \
    py3-psycopg2

ENV LIBRARY_PATH=/lib:/usr/lib
ENV APP_DIR=/app

# app dir
COPY requirements.txt ${APP_DIR}/requirements.txt
RUN pip3 install -r ${APP_DIR}/requirements.txt
RUN chown -R nginx:nginx ${APP_DIR} \
    && chmod 777 ${APP_DIR} -R \
    && chmod 777 /run/ -R \
    && chmod 777 /root/ -R
WORKDIR ${APP_DIR}

# expose web server port
# only http, for ssl use reverse proxy
EXPOSE 80

# copy config files into filesystem
COPY nginx.conf /etc/nginx/nginx.conf
COPY app.ini /app.ini
COPY entrypoint.sh /entrypoint.sh

# exectute start up script
ENTRYPOINT ["/entrypoint.sh"]
