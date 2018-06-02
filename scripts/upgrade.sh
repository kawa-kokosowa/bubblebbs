#!/bin/sh
# FIXME: this will be deleted soon because Docker isn't
# setup right yet for this repo.

echo "\nBuild new Docker image!\n"
docker-compose build

echo "\nStop any currently running bubblebbs containers...\n"
docker stop "$(docker ps -a -q  --filter ancestor=bubblebbs)"

echo "\nRun new image and serve!\n"
docker-compose run -d --rm -p 0.0.0.0:80:80 bubblebbs
