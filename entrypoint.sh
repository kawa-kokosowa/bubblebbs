#!/bin/bash

set -e

chown -R nginx:nginx ${APP_DIR} \
    && chmod 777 ${APP_DIR} -R \
    && chmod 777 /run/ -R \
    && chmod 777 /root/ -R

redis-server &

if [ "$1" == "debug" ]; then 
    echo "Running app in debug mode!"
    python3 -m bubblebbs.runserver
elif [ "$1" == "pytest" ]; then
    echo "Starting in pytest mode!"
    cd /app
    pytest -vv tests
else
    echo "Running app in production mode!"
    nginx && uwsgi --ini /app.ini
fi
