FROM python:3.8.6

COPY build/dist/*.whl /tmp/files/

RUN pip3 install /tmp/files/*.whl
    #rm -rf /tmp/files

CMD ["python3", "-m", "batch_sender.main"]
