# syntax=docker/dockerfile:1

FROM node:20-alpine AS frontend-build
WORKDIR /app/web

COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ ./
ENV VITE_API_BASE_URL=
RUN npm run build

FROM python:3.12-slim AS python-build
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip build
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m build --wheel --outdir /dist

FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MUSICBLOOM_DEMO_MODE=true
ENV MUSICBLOOM_API_HOST=0.0.0.0
ENV MUSICBLOOM_API_PORT=8000

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-build /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY static ./static
COPY --from=frontend-build /app/web/dist ./web/dist

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

CMD ["uvicorn", "musicbloom.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

FROM nginx:1.27-alpine AS frontend-runtime
COPY --from=frontend-build /app/web/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
