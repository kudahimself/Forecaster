# Backend image: Django + DRF + all science deps.
# Slim Python with manylinux wheels — no C toolchain needed.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependency layers cached across app-code changes.
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# SDK installed editable so the same `tracker` import works in tests + notebooks.
COPY sdk /app/sdk
RUN pip install -e /app/sdk

# App code
COPY backend /app/backend

# Data dir is a volume in compose; create the mount point so it exists
# on first run before the volume is attached.
RUN mkdir -p /app/data/artifacts /app/data/raw_cache

WORKDIR /app/backend

EXPOSE 8000

# Entrypoint: wait for the DB dir, apply migrations, then serve.
# Using runserver (not gunicorn) keeps the demo dependency-light;
# swap for gunicorn when hosting for real.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
