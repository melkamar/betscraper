FROM python:3.6.1
RUN pip install requests selenium

COPY ./install-phantomjs.sh /install-phantomjs.sh
RUN chmod +x /install-phantomjs.sh && /install-phantomjs.sh

ENV TZ=Europe/Prague
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["python", "/betscraper/betscraper.py"]
