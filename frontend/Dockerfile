FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_SEARCH_API_URL=http://localhost:8000/search
ARG VITE_USER_PREFERENCES_API=http://localhost:8000/userpreferences
ARG VITE_ALL_REPOS_ENDPOINT=/allrepos
ARG VITE_HIDDEN_GEMS_ENDPOINT=/hiddengem

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_SEARCH_API_URL=$VITE_SEARCH_API_URL \
    VITE_USER_PREFERENCES_API=$VITE_USER_PREFERENCES_API \
    VITE_ALL_REPOS_ENDPOINT=$VITE_ALL_REPOS_ENDPOINT \
    VITE_HIDDEN_GEMS_ENDPOINT=$VITE_HIDDEN_GEMS_ENDPOINT

RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
