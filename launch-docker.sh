#!/bin/bash

set -e

echo "WARNING:"
echo "I hope you're using the latest version of Docker and docker-compose!"
echo "Install according to the Docker CE website, not from your distro's repo!"

docker-compose build

if [ "$1" == "prod" ]; then 
    echo "Running app in production mode!"
    docker-compose run -d --rm -p 0.0.0.0:80:80 bubblebbs
elif [ "$1" == "pytest" ]; then
    echo "Run pytest in Docker container!"
    docker-compose run bubblebbs pytest
elif [ "$1" == "debug" ]; then
    echo "Run app in debug mode!"
    docker-compose run -d --rm -p 0.0.0.0:8080:8080 bubblebbs debug
fi
