# syntax=docker/dockerfile:1

# Stage 1: generate the static cultivos.json manifest from the image assets.
FROM python:3.13-slim AS manifest
WORKDIR /src
COPY utils/ utils/
COPY frontend/ frontend/
RUN python utils/generate_cultivos_manifest.py

# Stage 2: serve the static site (with generated manifest) via Nginx.
FROM nginx:1.27-alpine AS runtime
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=manifest /src/frontend/ /usr/share/nginx/html/

EXPOSE 80
