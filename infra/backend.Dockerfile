FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && useradd --system --uid 10001 --create-home modeloac
COPY --chown=modeloac:modeloac backend /app/backend
COPY --chown=modeloac:modeloac data /app/data
USER modeloac
WORKDIR /app/backend
RUN DJANGO_SECRET_KEY=build-only-not-runtime DATABASE_URL=sqlite:///:memory: python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn","config.wsgi:application","--no-control-socket","--bind","0.0.0.0:8000","--workers","2","--timeout","90","--access-logfile","-","--error-logfile","-"]
