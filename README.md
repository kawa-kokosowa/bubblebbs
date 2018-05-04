# bubblebbs

[![Build
Status](https://travis-ci.org/lily-mayfield/bubblebbs.svg?branch=master)](https://travis-ci.org/lily-mayfield/bubblebbs)

Text BBS/message board.

This project is in alpha. It is currently unversioned and very messy. It lacks
basic features like limiting, captcha, etc.

## General technical

Admins login at `/admin` with the default username `admin` and default password `admin`.

When you use docker at all be sure to `touch .env-file`.

## Production

You can also run the above locally to test out the production configuration for
bubblebbs.

`./launch-docker.sh prod`

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

`./launch-docker.sh pytest`

### Debugging in Docker

Run a server which reloads in a second within detecting
code changes:

`./launch-docker.sh debug`
