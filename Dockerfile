FROM python:3.10-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
COPY main.py /main.py

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]