#!/bin/bash
cd /root/betscraper
git pull

cd /root/
/usr/local/bin/docker-compose run betscraper
