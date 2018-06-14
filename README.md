# bubblebbs

[![Build
Status](https://travis-ci.org/lily-mayfield/bubblebbs.svg?branch=master)](https://travis-ci.org/lily-mayfield/bubblebbs)

Text BBS/message board which runs [bubblebbs.cafe](http://bubblebbs.cafe).

This project is in alpha. It is currently unversioned and very messy.

Features:

  * Cookie manager allows users to control name-remembering and custom
    stylesheets
  * Trip meta pages exist as soon as the tripcode is used when creating a post!
    You can edit these pages by supplying a string which hashes to that
    tripcode! Shows posts by that tripcode, as well as post counts!
  * Tripcodes salted by both secret *and* the poster's name. This prevents
    identity-jacking (in the event users happened to use the same password).
  * Flags IPs which use a name with a tripcode that doesn't match the original
    occurence of name's tripcode
  * Prefixes "verified" names with a green checkmark. Verified names are posts
    which have a tripcode matching the tripcode of the first post with said name.
  * Markdown support, optional headline syntax
  * Google Recaptcha
  * Create pages
  * Word filter lets you not only filter words (also pattern matches on
    plurals), but "flag" IP addresses that use those words
  * Automatically ban users based on certain phrases
  * Manage site through backend
  * Site blotter
  * Doesn't allow duplicate posts
  * Tripcodes hash to color and emoji
  * Fluid default stylesheet
  * Full text search

## General technical

Before you start:

  * Make sure you're using latest Docker and docker-compose, install according to
    Docker community instructions, don't install via your distribution's repo (it's
    probably way out-of-date!).
  * Docker will look for `.env-file`. So you need to `touch .env-file`. This
    includes setting up your Google Recaptcha info. Here are possible
    `.env-file` settings:
    * `BBBS_RECAPTCHA_SITE_KEY`
    * `BBBS_RECAPTCHA_SECRET_KEY`
    * `BBBS_SECRET_KEY`

There are multiple ways to run the app:

  * For production: Use Docker, `./launch-docker.sh prod`
  * To debug: either look at the "debugging without docker" section in this
    `README` or use `./launch-docker.sh debug`
  * Running tests: if you followed the "debugging without docker" section you
    can simply run `pytest` in the project root. Otherwise use
    `./launch-docker.sh pytest`.

Admins login at `/admin` with the default username `admin` and default password `admin`.

## Debugging without Docker

You can still fiddle around with `bubblebbs` like you would any ol' Python code:

  1. Create and activate a virtual environment
  1. `pip install -r requirements.txt`
  1. In Ubuntu I needed to `sudo apt install libssl-dev` (this is for `scrypt`)
  1. `python3 -m bubblebbs.runserver`
  1. http://localhost:8080/

You can run tests with `pytest` in the project root.

## Running HTTPS

Using this reverse proxy setup is really nice, it takes care of:

  * Running as many Docker services as you want behind this reverse-proxy,
    so it's easy to run many different websites on one machine!
  * Pain-free HTTPS!

Start by creating the `.letsencrypt` subdirectory of this project, where
everything will be stored.  Keep the absolute path to this directory handy.
Replace `/home/nuc/Server/bubblebbs/` with said absolute path in the commands
of this section.

Start the reverse proxy:

```
docker run -d -p 80:80 -p 443:443 \
    --name nginx-proxy \
    -v /home/nuc/Server/bubblebbs/.letsencrypt/certs:/etc/nginx/certs:ro \
    -v /home/nuc/Server/bubblebbs/.letsencrypt/vhosts:/etc/nginx/vhost.d \
    -v /home/nuc/Server/bubblebbs/.letsencrypt/challenge_files:/usr/share/nginx/html \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    --label com.github.jrcs.letsencrypt_nginx_proxy_companion.nginx_proxy \
    jwilder/nginx-proxy
```

Now start the reverse proxy HTTPS "companion:"

```
docker run -d \
    -v /home/nuc/Server/bubblebbs/.letsencrypt/certs:/etc/nginx/certs:rw \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    --volumes-from nginx-proxy \
    jrcs/letsencrypt-nginx-proxy-companion
```

Finally launch the BubbleBBS container:

```
docker run -e "BUBBLEBBS_BEHIND_REVERSE_PROXY=1" -e "VIRTUAL_HOST=bubblebbs.cafe" -e "LETSENCRYPT_HOST=bubblebbs.cafe" -e "LETSENCRYPT_EMAIL=lily.m.mayfield@gmail.com" -e "VIRTUAL_PORT=8081" --publish 8081:80 -d -v /home/nuc/Server/bubblebbs:/app --env-file .env-file --rm bubblebbs
```

Don't forget to forward ports 80 and 443 on your router or whatever!
