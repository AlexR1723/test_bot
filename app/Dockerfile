FROM python:3.10.9-bullseye
#WORKDIR /app
#ADD . /app
#CMD ["ls"]
COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt
CMD ["python", "/app/app.py"]
#EXPOSE 80
