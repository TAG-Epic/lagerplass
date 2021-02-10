FROM python:3.9
RUN pip install flask pillow qrcode pymongo
WORKDIR lagerplass
COPY . ./
ENV MONGO_URI=mongo
ENV SECURE=yes
CMD ["flask", "run", "--host", "0.0.0.0"]