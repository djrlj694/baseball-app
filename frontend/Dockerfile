FROM node:20-alpine

WORKDIR /app
COPY package.json .
RUN npm install

COPY . .
EXPOSE 5173
# /bin/sh is available by default in node:20-alpine
CMD ["npm", "run", "dev"]
