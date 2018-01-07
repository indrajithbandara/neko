#!/bin/bash

SERVICE_NAME=neko.service
BRANCH=dev

sudo -v
# Keeps sudo alive in case we are on a crappy internet connection
# or something takes a while to finish.
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

sudo systemctl stop ${SERVICE_NAME}
sudo systemctl status ${SERVICE_NAME}

git stash
git checkout ${BRANCH}
git pull --all
git stash apply

sudo systemctl start ${SERVICE_NAME}
sleep 5
sudo systemctl status ${SERVICE_NAME}

sudo -K
exit ${?}
