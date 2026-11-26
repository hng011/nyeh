FROM node:24-bookworm-slim AS build
# Astro inlines PUBLIC_* at build time, so they arrive as build args.
ARG PUBLIC_WS_ENDPOINT=wss://nyeh-agentik.kaktus.foo/ws_api/v1/chat
ARG PUBLIC_WS_CONFIG_PASSWORD_HASH=
ENV PUBLIC_WS_ENDPOINT=$PUBLIC_WS_ENDPOINT \
    PUBLIC_WS_CONFIG_PASSWORD_HASH=$PUBLIC_WS_CONFIG_PASSWORD_HASH
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
