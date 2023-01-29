FROM python:3.10.9-bullseye
#WORKDIR /app
#ADD . /app
#CMD ["ls"]
#RUN apt update \
#    && apt install postgresql-dev gcc python3-dev musl-dev
RUN pip install --upgrade pip
COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt
CMD ["python", "/app/app.py"]
#EXPOSE 80
