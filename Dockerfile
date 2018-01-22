FROM python:3.6.1
RUN pip install requests selenium

COPY ./install-phantomjs.sh /install-phantomjs.sh
RUN chmod +x /install-phantomjs.sh && /install-phantomjs.sh

CMD ["python", "/betscraper/betscraper.py"]
