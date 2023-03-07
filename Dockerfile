FROM python:3.11.2-slim-buster
WORKDIR /app
COPY . .
RUN pip install -U pip && pip install -r requirements.txt

CMD [ "python", "bot.py"]

