FROM python:3.9
RUN pip install flask pillow qrcode pymongo
WORKDIR lagerplass
COPY . ./
RUN ["flask", "run"]