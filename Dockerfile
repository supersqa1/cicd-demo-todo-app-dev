FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --uid 10001 --create-home appuser \
    && mkdir /app/tasks \
    && chown appuser:appuser /app/tasks
COPY app/ ./app/

USER appuser
EXPOSE 5151
CMD ["gunicorn", "--bind", "0.0.0.0:5151", "--workers", "1", "--threads", "4", "--access-logfile", "-", "--error-logfile", "-", "app.main:app"]
