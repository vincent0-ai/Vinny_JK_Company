# Use Python 3.12 for the backend (required by Django 6.0.1)
FROM python:3.12-slim

# Install Nginx and other dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Remove legacy deployment files to avoid confusion
RUN rm -f Fronted/Dockerfile Fronted/nginx.conf Fronted/captain-definition

# Configure Nginx
COPY nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Collect static files for Django Admin and Whitenoise
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
RUN python manage.py collectstatic --noinput

# Create a startup script to run migrations, setup permissions, Nginx, and Gunicorn
RUN echo "#!/bin/bash\n\
mkdir -p /app/data /app/media\n\
chmod -R 777 /app/data /app/media\n\
python manage.py migrate --noinput\n\
if [ \"\$DJANGO_SUPERUSER_USERNAME\" ]; then\n\
    python manage.py createsuperuser --noinput || true\n\
fi\n\
nginx -g 'daemon off;' &\n\
gunicorn vinny_kj.wsgi:application --bind 127.0.0.1:8000 --workers 3\n\
" > /app/start.sh
RUN chmod +x /app/start.sh

# Expose port 80 (Nginx)
EXPOSE 80

# Start services
CMD ["/app/start.sh"]
