FROM node:18-alpine

# Définir le répertoire de travail
WORKDIR /app

# Copier package.json et package-lock.json avant d'installer les dépendances
COPY package*.json ./

# Installer les dépendances sans recréer package-lock.json
RUN npm install

# Installer Angular CLI globalement
RUN npm install -g @angular/cli@17.3.3

# Copier le reste du code source
COPY . .

# Exposer le port utilisé par Angular
EXPOSE 4200

# Lancer Angular en mode développement avec watch (live reload)
CMD ["ng", "serve", "--host", "0.0.0.0", "--poll", "2000"]
