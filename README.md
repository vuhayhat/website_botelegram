# E-Commerce Store with Django

A complete e-commerce website built with Django and PostgreSQL.

## Features

- User authentication with phone number
- Google login integration (to be implemented)
- Custom admin panel for managing products and categories
- Responsive design with Bootstrap 5
- PostgreSQL database integration

## Requirements

- Python 3.8+
- Django 5.2+
- PostgreSQL
- psycopg2-binary

## Installation

1. Clone the repository
```bash
git clone <repository-url>
cd ecommerce-store
```

2. Create a virtual environment and activate it
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create PostgreSQL database
```bash
# Log into PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE ecommerce_db;
```

5. Update database settings in `ecommerce/settings.py` if needed
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ecommerce_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

6. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

7. Create a superuser
```bash
python manage.py createsuperuser
```

8. Run the development server
```bash
python manage.py runserver
```

9. Access the website at http://127.0.0.1:8000/

## Project Structure

- `ecommerce/`: Main project settings
- `store/`: Main app for products and categories
- `accounts/`: User authentication and management
- `admin_panel/`: Custom admin interface
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS, images)
- `media/`: User uploaded files

## Usage

1. Admin Panel: Access at http://127.0.0.1:8000/admin/
2. User Registration: http://127.0.0.1:8000/accounts/register/
3. User Login: http://127.0.0.1:8000/accounts/login/ 