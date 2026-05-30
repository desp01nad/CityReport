FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY admin_dashboard ./admin_dashboard
COPY db_repository ./db_repository
RUN pip install --no-cache-dir -r admin_dashboard/requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "admin_dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
