# Use an official Node image as the build environment
FROM node:18-alpine as build
RUN mkdir /app
WORKDIR /app

# Copy the package files and install dependencies
COPY package*.json /app/
RUN npm install


# Installer Angular CLI globalement pour que 'ng' soit disponible
RUN npm install -g @angular/cli@17.3.3

# Copy the rest of the app source code
COPY . .

# Build the Angular app
RUN npm run build

# Use NGINX to serve the app
FROM nginx:alpine
# Copy the build output to the NGINX html directory
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

# Copy the NGINX configuration file
COPY nginx.conf /etc/nginx/nginx.conf

# Expose the NGINX port
EXPOSE 80

