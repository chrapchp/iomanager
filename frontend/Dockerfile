<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *************************************************-->

# Stage 1: build Nuxt 3 application
FROM node:20-slim AS builder

WORKDIR /app

# Layer: dependencies (cache-friendly)
COPY package*.json ./
RUN npm ci

# Layer: source + build
COPY . .
RUN npm run build


# Stage 2: lean production image (no source, no devDependencies)
FROM node:20-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
