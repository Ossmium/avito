FROM python:3.11.3

WORKDIR /usr/src/app

RUN pip install --upgrade pip
COPY ./req.txt /usr/src/app/
RUN pip install -r req.txt

EXPOSE 8080

ENV PYTHONUNBUFFERED=1
ENV POSTGRES_CONN=postgresql+asyncpg://cnrprod1725723225-team-78723:cnrprod1725723225-team-78723@rc1b-5xmqy6bq501kls4m.mdb.yandexcloud.net:6432/cnrprod1725723225-team-78723

COPY . /usr/src/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]