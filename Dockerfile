FROM node:18-bullseye AS assets

WORKDIR /app/

COPY package.json package-lock.json ./
RUN npm ci

COPY webpack.mix.js ./
COPY static/src/ static/src/

RUN npx mix

FROM python:3.10-slim-bullseye AS builder

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends libcairo2-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.10-slim-bullseye AS runtime

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

COPY --from=builder /install /usr/local

COPY . .
COPY --from=assets /app/static/build /app/static/build

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["python3", "manage.py", "runserver"]
