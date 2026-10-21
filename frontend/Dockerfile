FROM node:22-alpine AS build
WORKDIR /app/frontend
RUN npm install --global pnpm@11.19.0
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
COPY docs/evaluation-run06.md docs/person1-neural-handoff.md /app/docs/
RUN pnpm build
FROM nginxinc/nginx-unprivileged:stable-alpine
COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
