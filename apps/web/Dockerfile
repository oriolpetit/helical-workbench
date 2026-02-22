# Stage 1: build the static site
# Build context must be the repo root (monorepo)
FROM node:22-alpine AS builder

WORKDIR /app

# Copy root lockfile and package manifests needed for workspace resolution
COPY package.json package-lock.json ./
COPY packages/typescript-config/package.json ./packages/typescript-config/
COPY packages/eslint-config/package.json ./packages/eslint-config/
COPY apps/web/package.json ./apps/web/

RUN npm ci

# Copy source
COPY packages/ ./packages/
COPY apps/web/ ./apps/web/

RUN npm run build --workspace=web

# Stage 2: serve with nginx
FROM nginx:alpine

COPY --from=builder /app/apps/web/out /usr/share/nginx/html

EXPOSE 80
