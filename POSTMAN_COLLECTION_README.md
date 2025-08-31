# Bill Payment API - Postman Collection

This directory contains a comprehensive Postman collection for testing the Bill Payment API. The collection includes all available endpoints with proper authentication, rate limiting considerations, and automated token management.

## Files Included

- `Bill_Payment_API.postman_collection.json` - Main Postman collection with all API endpoints
- `Bill_Payment_API.postman_environment.json` - Environment variables for local development
- `POSTMAN_COLLECTION_README.md` - This documentation file

## Quick Setup

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button
3. Select both JSON files:
   - `Bill_Payment_API.postman_collection.json`
   - `Bill_Payment_API.postman_environment.json`
4. Select the "Bill Payment API - Local Development" environment

### 2. Start the API Server

Ensure your Django development server is running:

```bash
cd /path/to/BillPaymentApi
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000`

### 3. Test the Collection

1. Start with **User Registration** to create a test account
2. Use **User Login** to authenticate and get JWT tokens
3. Test other endpoints with the automatically set tokens

## Collection Structure

The collection is organized into the following folders:

### 🔐 Authentication
- **User Registration** - Create new user accounts
- **User Login** - Authenticate and receive JWT tokens (auto-saves tokens)
- **User Logout** - Logout and blacklist refresh token

### 👤 User Profile
- **Get User Profile** - Retrieve authenticated user's profile
- **Update User Profile** - Update user information

### 🔑 Password Reset
- **Forgot Password** - Request password reset email
- **Verify Reset Token** - Validate reset token
- **Reset Password** - Change password with valid token

### 🎫 JWT Token Management
- **Obtain JWT Token Pair** - Get access/refresh tokens (alternative to login)
- **Refresh JWT Token** - Refresh expired access token
- **Verify JWT Token** - Validate token status

### 📚 API Documentation
- **Swagger UI Documentation** - Interactive API docs
- **ReDoc Documentation** - Alternative API docs
- **OpenAPI Schema** - Raw schema JSON

## Environment Variables

The collection uses the following environment variables:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://127.0.0.1:8000` | API base URL |
| `user_email` | `test@example.com` | Test user email |
| `user_password` | `TestPassword123!` | Test user password |
| `new_password` | `NewPassword123!` | New password for reset testing |
| `reset_token` | *(empty)* | Password reset token |
| `access_token` | *(empty)* | JWT access token (auto-set) |
| `refresh_token` | *(empty)* | JWT refresh token (auto-set) |

### Customizing Variables

1. Click the environment name in Postman
2. Modify values as needed:
   - Change `base_url` for different environments
   - Update `user_email` and `user_password` for your test account
   - Set `reset_token` when testing password reset flow

## Automated Features

### Token Management

The collection includes automated scripts that:

- **Auto-save tokens**: Login requests automatically save `access_token` and `refresh_token`
- **Auto-refresh**: Token refresh requests update the `access_token`
- **Auto-authentication**: Authenticated endpoints use the saved `access_token`

### Rate Limiting Awareness

The API implements rate limiting on authentication endpoints:

- **Login**: 5 requests per minute
- **Forgot Password**: 3 requests per minute
- **Reset Password**: 3 requests per minute
- **Verify Reset Token**: 10 requests per minute

If you hit rate limits, wait for the time window to reset before retrying.

## Testing Workflows

### Complete User Registration Flow

1. **User Registration** → Creates account and returns tokens
2. **Get User Profile** → Verify account details
3. **Update User Profile** → Test profile updates

### Authentication Flow

1. **User Login** → Get JWT tokens
2. **Verify JWT Token** → Validate access token
3. **Refresh JWT Token** → Get new access token
4. **User Logout** → Blacklist refresh token

### Password Reset Flow

1. **Forgot Password** → Request reset email
2. **Verify Reset Token** → Check token validity
3. **Reset Password** → Change password with token
4. **User Login** → Test new password

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Check if `access_token` is set in environment
- Try refreshing the token or logging in again
- Verify the token hasn't expired

**429 Too Many Requests**
- You've hit the rate limit
- Wait for the rate limit window to reset
- Check the endpoint's specific rate limit

**400 Bad Request**
- Verify request body format and required fields
- Check if email format is valid
- Ensure password meets requirements

**500 Internal Server Error**
- Check if the Django server is running
- Verify database connection
- Check server logs for detailed error information

### Environment-Specific Setup

**Production Environment**
1. Create a new environment in Postman
2. Update `base_url` to your production URL
3. Use HTTPS URLs for production
4. Update authentication credentials

**Docker Environment**
1. If using Docker, update `base_url` to `http://localhost:8000`
2. Ensure Docker containers are running
3. Check port mappings in docker-compose.yml

## API Features Covered

✅ **User Management**
- Registration with email validation
- Profile retrieval and updates
- Email-based authentication

✅ **JWT Authentication**
- Token generation and refresh
- Token validation and verification
- Secure logout with token blacklisting

✅ **Password Reset**
- Email-based reset requests
- Token validation
- Secure password updates

✅ **Security Features**
- Rate limiting on sensitive endpoints
- JWT token expiration handling
- Secure password requirements

✅ **API Documentation**
- Interactive Swagger UI
- ReDoc documentation
- OpenAPI schema access

## Additional Resources

- **API Documentation**: Visit `http://127.0.0.1:8000/api/docs/` for interactive docs
- **Project README**: See main `README.md` for setup and deployment instructions
- **Django Admin**: Access `http://127.0.0.1:8000/admin/` for database management

## Support

If you encounter issues with the Postman collection:

1. Verify the Django server is running
2. Check environment variable values
3. Review the API documentation at `/api/docs/`
4. Check the main project README for setup instructions

---

**Happy Testing! 🚀**

This collection provides a complete testing suite for the Bill Payment API. Use it to explore all features, test integrations, and validate your API implementations.