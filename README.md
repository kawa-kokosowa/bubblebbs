# bubblebbs

[![Build
Status](https://travis-ci.org/lily-mayfield/bubblebbs.svg?branch=master)](https://travis-ci.org/lily-mayfield/bubblebbs)

One-board imageboard where only verified tripcodes can post images and start
threads (everyone else may only reply to threads with text).

## General technical

This project is in alpha, it is poorly documented and very messy, it is not
recommended for production.

Admins login at `/admin` with the default username `admin` and default password `admin`.

When you run docker you can see the IP it's listening on by using `docker
inspect containername`.

The default verified tripcode is `lol` so put something like `name#lol` in the
name field when posting.

## Production

You can also run the above locally to test out the production configuration for
bubblebbs.

`docker-compose build; docker-compose run -d --rm -p 0.0.0.0:80:80 bubblebbs`

## Testing

It's nice to run tests in Docker way because it eliminates the requirement of setting
up/installing dependencies and the like.

### Host

You can still fiddle around with `bubblebbs` like you would any ol' Python code:

  1. Create and activate a virtual environment
  1. `pip install -r requirements.txt`
  1. In Ubuntu I needed to `sudo apt install libssl-dev` (this is for `scrypt`)
  1. `python3 -m bubblebbs.runserver`
  1. http://localhost:8080/

You can run tests with `pytest` in the project root.

### Run tests in Docker

`docker-compose build && docker-compose run bubblebbs pytest`

### Debugging in Docker

Run a server which reloads in a second within detecting
code changes:

`docker-compose build && docker-compose run -d --rm -p 0.0.0.0:8080:8080 bubblebbs debug`
