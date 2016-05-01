FROM python:2.7-alpine

ADD . /code

WORKDIR /code

RUN pip install -r requirements.txt

EXPOSE "5000"
CMD ["python", "app.py"]
