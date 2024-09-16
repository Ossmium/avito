FROM python:3.11.3

WORKDIR /usr/src/app

RUN pip install --upgrade pip
COPY ./req.txt /usr/src/app/
RUN pip install -r req.txt

EXPOSE 8080

ENV PYTHONUNBUFFERED=1

COPY . /usr/src/app/

CMD ["uvicorn", "app.main:app", "--port", "8080", "--reload"]