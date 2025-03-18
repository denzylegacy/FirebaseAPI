<div align="center">
  <!-- Here you would add a logo image if available -->
  <!-- <img src="docs/assets/firebase-api-logo.png" alt="Firebase API Logo" width="200" style="border-radius: 50%; object-fit: cover;"/> -->

  # Secure Firebase API

  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=flat&logo=firebase&logoColor=black)](https://firebase.google.com/)
  [![JWT](https://img.shields.io/badge/JWT-000000?style=flat&logo=json-web-tokens&logoColor=white)](https://jwt.io/)

  A highly secure and performant API for Firebase Realtime Database operations with comprehensive access control and data validation.
</div>

## Features

- **Secure Authentication** - JWT-based user authentication with bcrypt password hashing
- **Complete CRUD Operations** - Full API for Create, Read, Update, Delete operations on Firebase
- **Rate Limiting** - Protects against brute force and DoS attacks
- **Data Validation** - Comprehensive schema validation using Pydantic
- **Request Logging** - Detailed activity logging for security auditing
- **CORS Protection** - Configurable cross-origin resource sharing
- **Automatic Documentation** - Interactive API documentation via Swagger UI
- **Async Architecture** - Built on async I/O for high concurrency and performance

## How It Works

### Security Architecture

The API implements multiple layers of security:

1. **Authentication Layer**: JWT tokens verify user identity with configurable expiration
2. **Authorization Middleware**: Validates tokens for protected routes
3. **Rate Limiting**: Token bucket algorithm prevents abuse
4. **Input Validation**: All inputs are validated through Pydantic models
5. **Secure Password Storage**: Passwords stored with bcrypt hashing

### Async Firebase Integration

The system uses a singleton-based async Firebase client that:

1. **Manages Connections**: Efficiently maintains database connections
2. **Handles Authentication**: Manages Firebase credentials securely
3. **Provides Context Managers**: Safe resource handling with async context managers
4. **Maps Errors**: Translates Firebase errors to appropriate HTTP responses

### Data Flow

1. **Request Reception**: FastAPI receives and validates incoming requests
2. **Authentication Check**: Middleware verifies JWT tokens
3. **Rate Limit Check**: Requests are checked against rate limits
4. **Data Validation**: Input data is validated against Pydantic schemas
5. **Firebase Operation**: Request is passed to the Firebase service layer
6. **Response Formation**: Results are formatted and returned to the client
7. **Logging**: All operations are logged for audit purposes

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/firebase-api.git
   cd firebase-api
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Or install packages individually:
   ```bash
   pip install fastapi>=0.95.0 uvicorn>=0.21.1 pydantic>=1.10.7 firebase-admin>=6.1.0 python-jose[cryptography]>=3.3.0 passlib[bcrypt]>=1.7.4 python-multipart>=0.0.6
   ```

4. Set up your Firebase:
   - Create a Firebase project in the [Firebase Console](https://console.firebase.google.com/)
   - Generate a service account key (Project Settings > Service Accounts > Generate New Private Key)
   - Save the JSON file to `firebase_client/firebase-cert.json`

5. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your Firebase configuration and security settings.

## Running the API

1. Start the server:
   ```bash
   uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Usage

### Authentication

To use the API, you first need to authenticate:

```bash
# Get a JWT token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password"
```

This will return a JWT token:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### CRUD Operations

Use the token for authenticated requests:

```bash
# Get all items in a collection
curl -X GET "http://localhost:8000/api/v1/data/users" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get a specific item
curl -X GET "http://localhost:8000/api/v1/data/users/user123" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Create a new item
curl -X POST "http://localhost:8000/api/v1/data/users" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "description": "New user"}'

# Update an item
curl -X PUT "http://localhost:8000/api/v1/data/users/user123" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Updated"}'

# Delete an item
curl -X DELETE "http://localhost:8000/api/v1/data/users/user123" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Configuration

The API can be configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Application environment | `development` |
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-change-in-production` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `RATE_LIMIT_RATE` | Requests allowed per time period | `60` |
| `RATE_LIMIT_PER` | Time period in seconds for rate limiting | `60` |
| `FIREBASE_URL` | Firebase database URL | `https://yoruichi-99389-default-rtdb.firebaseio.com/` |
| `FIREBASE_CERT_FILE_PATH` | Path to Firebase certificate | `firebase_client/firebase-cert.json` |

## Project Structure

```
app/
├── api/
│   ├── main.py            # FastAPI application
│   ├── middleware/        # Auth and rate limiting middleware
│   ├── models/            # Pydantic schemas
│   ├── routes/            # API route definitions
│   └── security/          # JWT implementation
├── services/
│   └── firebase_client/   # Firebase integration
│       ├── async_firebase.py  # Async Firebase client
│       └── data_service.py    # Service layer for data operations
└── settings.py            # Configuration
```

## Security Best Practices

1. **Change Default Credentials**: Update the default admin password immediately
2. **Use HTTPS**: In production, always serve the API over HTTPS
3. **Set Strong SECRET_KEY**: Use a strong, unique SECRET_KEY for JWT signing
4. **Restrict CORS**: Configure CORS_ORIGINS to only allow trusted domains
5. **Adjust Rate Limits**: Tune rate limiting based on your expected traffic patterns
6. **Secure Firebase Rules**: Configure Firebase Database Rules for additional security

## Deployment

For production deployment, consider:

1. Using a process manager like Gunicorn with Uvicorn workers
2. Setting up HTTPS termination via Nginx or a load balancer
3. Implementing proper logging with log rotation
4. Using a secure environment variables management system

Example with Docker:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

This project provides a secure, high-performance API for Firebase operations. Use it as a foundation for your applications requiring secure data storage and retrieval. 