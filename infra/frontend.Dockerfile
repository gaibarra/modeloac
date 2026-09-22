FROM node:22-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL NEXT_TELEMETRY_DISABLED=1
RUN npm run build
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
RUN addgroup -S -g 10001 modeloac && adduser -S -u 10001 -G modeloac modeloac
COPY --from=builder --chown=modeloac:modeloac /app/.next/standalone ./
COPY --from=builder --chown=modeloac:modeloac /app/.next/static ./.next/static
COPY --from=builder --chown=modeloac:modeloac /app/public ./public
USER modeloac
EXPOSE 3000
CMD ["node","server.js"]
