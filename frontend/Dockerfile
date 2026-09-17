FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ARG VITE_API_URL=/api/v1
ARG VITE_APP_NAME="Team Building Portal"
ARG VITE_APP_ENV=production
ARG VITE_ENABLE_QUERY_DEVTOOLS=false
ARG VITE_GALA_POLLING_INTERVAL=3000
ARG VITE_API_TIMEOUT=30000

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_NAME=$VITE_APP_NAME
ENV VITE_APP_ENV=$VITE_APP_ENV
ENV VITE_ENABLE_QUERY_DEVTOOLS=$VITE_ENABLE_QUERY_DEVTOOLS
ENV VITE_GALA_POLLING_INTERVAL=$VITE_GALA_POLLING_INTERVAL
ENV VITE_API_TIMEOUT=$VITE_API_TIMEOUT

RUN npm run build


FROM nginx:1.27-alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
