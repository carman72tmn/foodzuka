FROM php:8.4-fpm-alpine

# Set working directory
WORKDIR /var/www/html

# Install dependencies
RUN apk add --no-cache \
    postgresql-dev \
    libpng-dev \
    libzip-dev \
    oniguruma-dev \
    git \
    unzip \
    nodejs \
    npm

# Install PHP extensions
RUN docker-php-ext-install pdo pdo_pgsql pgsql gd zip mbstring

# Get Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Copy application files
COPY . .

# Install PHP and JS dependencies
RUN composer install
RUN npm install

EXPOSE 8000 5173

# Entrypoint script would be better, but for simplicity:
CMD ["php", "artisan", "serve", "--host", "0.0.0.0", "--port", "8000"]
