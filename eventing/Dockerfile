FROM python:3.6-slim

RUN pip install requests Flask flask-cors

ENV APP_HOME /app
COPY . $APP_HOME
WORKDIR $APP_HOME

ENTRYPOINT ["python"]
CMD ["app.py"]
