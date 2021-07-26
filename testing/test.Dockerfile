FROM python:3.8.6

COPY mock-server.py /tmp/mock-server.py

RUN pip install fastapi uvicorn python-multipart
WORKDIR /tmp

CMD ["python", "mock-server.py"]
