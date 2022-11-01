# syntax=docker/dockerfile:1
FROM python:3.9
MAINTAINER Dimagi <devops@dimagi.com>

ENV PYTHONUNBUFFERED=1 \
    PYTHONUSERBASE=/vendor \
    PATH=/vendor/bin:$PATH \
    NODE_VERSION=14.19.1

RUN groupadd -r cchq && \
    useradd -r -g cchq cchq

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        default-jdk \
        wget \
        libxml2-dev \
        libxmlsec1-dev \
        libxmlsec1-openssl \
        gettext

# Deletes all package sources, so don't apt-get install anything after this:
RUN rm -rf /var/lib/apt/lists/* /src/*.deb

# Install Node
RUN curl -SLO "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.gz" && \
    tar -xzf "node-v$NODE_VERSION-linux-x64.tar.gz" -C /usr/local --strip-components=1 && \
    rm "node-v$NODE_VERSION-linux-x64.tar.gz"

RUN npm -g install \
    yarn \
    bower \
    grunt-cli \
    uglify-js

WORKDIR /vendor
COPY . /vendor/

#COPY requirements/prod-requirements.txt /vendor/requirements.txt
# prefer https for git checkouts made by pip
RUN git config --global url."https://".insteadOf git:// && \
    pip install --upgrade pip && \
    pip install -r requirements/prod-requirements.txt --user --upgrade && \
    rm -rf /root/.cache/pip

#COPY package.json /vendor/
RUN npm shrinkwrap && \
    yarn global add phantomjs-prebuilt

#COPY . /vendor/
RUN python manage.py collectstatic --noinput
