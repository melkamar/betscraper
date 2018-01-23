#!/bin/bash
while true; do
	cd /root/betscraper 
	git pull >> /var/log/betscraper.log 2>>/var/log/betscraper.log

	cd /root/
	/usr/local/bin/docker-compose run betscraper  >> /var/log/betscraper.log 2>>/var/log/betscraper.log

	sleep 2
done
