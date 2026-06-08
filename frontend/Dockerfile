# FleetCare frontend — multi-stage build (node build → nginx:alpine)
# Stav: VO VÝVOJI — nepoužívať v produkcii bez revízie.

# ── Stage 1: build ────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

# Build-time API base (injected as VITE_API_BASE, default /api)
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE

# Build version (yyyymmddhhmm), injected by CI; "dev" for local builds.
ARG VITE_BUILD_VERSION=dev
ENV VITE_BUILD_VERSION=$VITE_BUILD_VERSION

COPY package.json package-lock.json* ./
RUN npm ci || npm install

COPY . .
RUN npm run build

# ── Stage 2: serve ────────────────────────────────────────────────────
FROM nginx:alpine AS serve
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
