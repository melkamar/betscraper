FROM python:3.6.1
RUN pip install requests selenium

RUN chmod +x /betscraper/install-phantomjs.sh

CMD ["python", "/betscraper/betscraper.py"]
