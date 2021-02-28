FROM python:3.8

ENV BOT_TOKEN=""
ENV BOT_NAME=""
ENV TZ=Europe/Minsk
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mkdir -p /home/bot
WORKDIR /home/bot
COPY . /home/bot
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "server.py"]
