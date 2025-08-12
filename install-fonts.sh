#!/bin/bash
# Install fonts during deployment
apt-get update
apt-get install -y fontconfig fonts-dejavu fonts-liberation fonts-ubuntu
fc-cache -fv
