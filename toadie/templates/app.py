FROM {{python:alpine}}
RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app/
RUN pip install --no-cache-dir --upgrade -r requirements.txt
ADD . /app/
CMD ['/app/run.sh']
EXPOSE 8000
