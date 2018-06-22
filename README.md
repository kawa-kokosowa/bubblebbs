# BubbleBBS

[![Build
Status](https://travis-ci.org/lily-mayfield/bubblebbs.svg?branch=master)](https://travis-ci.org/lily-mayfield/bubblebbs)

Text BBS/message board which runs [bubblebbs.cafe](http://bubblebbs.cafe).

This project is in alpha. It is currently unversioned and very messy.

Some of BubbleBBS' features:

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

## You must do this before you begin

  * Make sure you're using latest Docker and docker-compose, install according to
    Docker community instructions, don't install via your distribution's repo (it's
    probably way out-of-date!).
  * Docker will look for `.env-file` unless you provide docker
    with envvars using `-e ENVVAR=value`. So you need to do either:

    ```cp .env-file.debug.example .env-file```

    or

    ```cp .env-file.prod.example .env-file```

    And then edit `.env-file`.

## General technical notes
    
Admins login at `/admin` with the default username `admin` and default password `admin`.
Make sure to change this!

### Running tests

```
docker build . -t bubblebbs
docker run bubblebbs pytest -v "$(pwd):/app"
```

You only need to run `docker build` once, but you need to run it again when/if
`Dockerfile` changes.

### Debugging

To make a debugging server which reloads on changes run on
http://<docker-ip>:8080 (generally it's http://172.17.0.2:8080/) do something
like this:

```
docker build . -t bubblebbs
docker run -it \
    -p 8080:8080 \
    -v "$(pwd):/app" \
    --env-file .env-file
    bubblebbs debug
```

To find out the address the debug server is running on you can use this (but
replace `containerid` with the id of the container created in last step):

```
docker inspect -f "{{ .NetworkSettings.IPAddress }}" containerid
```

You only need to run `docker build` once, but you need to run it again when/if
`Dockerfile` changes.

## Debugging, running tests without Docker

You can still fiddle around with `bubblebbs` like you would any ol' Python code:

  1. Create and activate a virtual environment
  1. `pip install -r requirements.txt`
  1. In Ubuntu I needed to `sudo apt install libssl-dev` (this is for `scrypt`)
  1. `python3 -m bubblebbs.runserver`
  1. http://localhost:8080/

You can run tests with `pytest` in the project root.

## Running production with HTTPS

Using this reverse proxy setup is really nice, it takes care of:

  * Running as many Docker services as you want behind this reverse-proxy,
    so it's easy to run many different websites on one machine!
  * Pain-free HTTPS!

You will need a .letsencrypt directory to hold HTTPS stuff. It'll get mounted
to various places in a couple containers.

Start the reverse proxy, you can copy and paste the following:

```
docker run -d -p 80:80 -p 443:443 \
    --name nginx-proxy \
    -v "$(pwd)/.letsencrypt/certs:/etc/nginx/certs:ro" \
    -v "$(pwd)/.letsencrypt/vhosts:/etc/nginx/vhost.d" \
    -v "$(pwd)/.letsencrypt/challenge_files:/usr/share/nginx/html" \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    --label com.github.jrcs.letsencrypt_nginx_proxy_companion.nginx_proxy \
    jwilder/nginx-proxy
```

Once you've started `nginx-proxy` you can bring it back up with `docker start
nginx-proxy` if it ever goes down.

Now start the reverse proxy HTTPS "companion," you can simply copy and paste
this:

```
docker run -d \
    -v "$(pwd)/.letsencrypt/certs:/etc/nginx/certs:rw" \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    --volumes-from nginx-proxy \
    jrcs/letsencrypt-nginx-proxy-companion
```

Build the BubbleBBS container, you can copy and paste this:

```
docker build . -t bubblebbs
```

Finally launch the BubbleBBS container, but please take special care to use
your information (don't just paste this!):

```
docker run \
    -e "BBBS_BEHIND_REVERSE_PROXY=1" \
    -e "VIRTUAL_HOST=bubblebbs.cafe" \
    -e "LETSENCRYPT_HOST=bubblebbs.cafe" \
    -e "LETSENCRYPT_EMAIL=lily.m.mayfield@gmail.com" \
    -e "VIRTUAL_PORT=8081" \
    --publish 8081:80 \
    -d \
    -v "$(pwd)/bubblebbs/bubblebbs.db:/app/bubblebbs/bubblebbs.db" \
    --env-file .env-file \
    --name bbbsd
    bubblebbs
```

You can relaunch with `docker up bbbsd`.  You don't need an `env-file` you can
just use `-e` for all the envvars instead (especially useful if you're using
AWS ECS!).  Also if you're not using sqlite3 you can remove `-v
"$(pwd)/bubblebbs/bubblebbs.db:bubblebbs/bubblebbs.db"`.
