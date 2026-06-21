FROM python:3.11-slim

WORKDIR /project

COPY requirements.txt /project/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /project/backend

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/project

EXPOSE 8000

CMD ["gunicorn", "backend.app:app", "-b", "0.0.0.0:8000", "--workers=1"]