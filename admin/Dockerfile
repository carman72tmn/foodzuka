# PHP Application
FROM php:8.4-fpm-alpine
WORKDIR /var/www/html

# Install system dependencies
RUN apk add --no-cache \
    postgresql-dev \
    libpng-dev \
    libzip-dev \
    oniguruma-dev \
    unzip \
    && docker-php-ext-install pdo pdo_pgsql pgsql gd zip mbstring

# Get Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Copy application files
COPY . .

# Copy pre-built frontend assets
# This requires the 'build' folder to exist in 'admin/public/build' locally
COPY public/build ./public/build

# Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader

EXPOSE 9000
CMD ["php-fpm"]
