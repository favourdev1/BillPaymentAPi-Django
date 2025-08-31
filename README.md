# Bill Payment API

A comprehensive Django REST API for bill payment management with user authentication, JWT tokens, and password reset functionality.

## Features

- **User Management**: Custom user model with email-based authentication
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Password Reset**: Email-based password reset with Redis token storage
- **API Documentation**: Interactive Swagger/OpenAPI documentation
- **Database Support**: PostgreSQL for production, SQLite for development
- **Redis Integration**: Token storage and caching
- **Email Integration**: Password reset emails
- **Security**: CORS support, secure headers, and password validation

## Tech Stack

- **Backend**: Django 4.2.23, Django REST Framework
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL (production), SQLite (development)
- **Cache/Storage**: Redis
- **Documentation**: drf-spectacular (Swagger/OpenAPI)
- **Email**: Django email backend

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL (for production)
- Redis (for production)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BillPaymentApi
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   ```bash
   cp .env.example .env  # Create from template
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost:5432/billpayment_db
DB_NAME=billpayment_db
DB_USER=username
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
PASSWORD_RESET_TIMEOUT=3600
```

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/api/auth/register/` | User registration | None |
| POST | `/api/auth/login/` | User login | None |
| POST | `/api/auth/logout/` | User logout | Required |
| GET/PUT | `/api/auth/profile/` | User profile | Required |

### Password Reset Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/api/auth/forgot-password/` | Request password reset | None |
| POST | `/api/auth/reset-password/` | Reset password with token | None |
| POST | `/api/auth/verify-reset-token/` | Verify reset token | None |

### JWT Token Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/api/auth/token/` | Obtain JWT token pair | None |
| POST | `/api/auth/token/refresh/` | Refresh access token | None |
| POST | `/api/auth/token/verify/` | Verify token validity | None |

### Documentation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/docs/` | Swagger UI documentation |
| GET | `/api/redoc/` | ReDoc documentation |
| GET | `/api/schema/` | OpenAPI schema |

## API Usage Examples

### User Registration

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
  }'
```

### User Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Forgot Password

```bash
curl -X POST http://localhost:8000/api/auth/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

### Reset Password

```bash
curl -X POST http://localhost:8000/api/auth/reset-password/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "token": "reset-token-from-email",
    "new_password": "newsecurepassword123",
    "confirm_password": "newsecurepassword123"
  }'
```

### Authenticated Request

```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer your-access-token"
```

## Database Configuration

### Development (SQLite)

The project is configured to use SQLite by default for development. No additional setup required.

### Production (PostgreSQL)

1. **Install PostgreSQL**
2. **Create database and user**
   ```sql
   CREATE DATABASE billpayment_db;
   CREATE USER username WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE billpayment_db TO username;
   ```
3. **Update settings.py** to use PostgreSQL configuration
4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

## Redis Configuration

### Development

Redis is optional for development. The application will fall back to in-memory storage.

### Production

1. **Install Redis**
2. **Start Redis server**
   ```bash
   redis-server
   ```
3. **Update environment variables** with Redis connection details

## Testing

### Run Tests

```bash
python manage.py test
```

### API Testing

Use the interactive API documentation at:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Deployment

### Production Checklist

1. **Environment Variables**
   - Set `DEBUG=False`
   - Configure production database
   - Set secure `SECRET_KEY`
   - Configure email settings
   - Set proper `ALLOWED_HOSTS`

2. **Database**
   - Use PostgreSQL
   - Run migrations
   - Create superuser

3. **Static Files**
   ```bash
   python manage.py collectstatic
   ```

4. **Security**
   - Enable HTTPS
   - Configure CORS properly
   - Set secure headers

### Docker Deployment (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### Heroku Deployment

1. **Install Heroku CLI**
2. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```
3. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DEBUG=False
   # ... other variables
   ```
4. **Deploy**
   ```bash
   git push heroku main
   ```

## Project Structure

```
BillPaymentApi/
├── Billpayment/          # Main project directory
│   ├── __init__.py
│   ├── settings.py       # Django settings
│   ├── urls.py          # Main URL configuration
│   ├── wsgi.py          # WSGI configuration
│   └── asgi.py          # ASGI configuration
├── accounts/            # User management app
│   ├── models.py        # User model
│   ├── serializers.py   # API serializers
│   ├── views.py         # API views
│   ├── urls.py          # App URL configuration
│   ├── admin.py         # Admin configuration
│   ├── utils.py         # Utility functions
│   └── migrations/      # Database migrations
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── manage.py           # Django management script
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository.