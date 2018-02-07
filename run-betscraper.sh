#!/bin/bash
while true; do
        (cd /betscraper && git pull)
        python  /betscraper/betscraper.py>> /var/log/betscraper.log 2>>/var/log/betscraper.log
	sleep 10
done
