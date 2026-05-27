FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY user_api ./user_api
COPY db_repository ./db_repository
RUN pip install --no-cache-dir -r user_api/requirements.txt

EXPOSE 5000

CMD ["flask", "--app", "user_api.app", "run", "--host=0.0.0.0", "--port=5000"]
