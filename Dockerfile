FROM python:2.7
RUN apt-get update && apt-get install -y \
        libxml2 \
        libxml2-dev \
        libxslt1.1 \
        libxslt-dev
WORKDIR /app
EXPOSE 5000
COPY ./requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir --disable-pip-version-check
COPY . /app
RUN python setup.py develop
