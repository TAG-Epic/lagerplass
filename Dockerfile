FROM python:3.9
RUN pip install flask pillow qrcode
WORKDIR lagerplass
COPY . ./
RUN ["flask", "run"]