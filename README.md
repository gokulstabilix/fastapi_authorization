# Authorization Service (FastAPI + PostgreSQL + Redis)

An enterprise-grade authorization service built with FastAPI, featuring a robust REST API, PostgreSQL persistence for user data, and Redis for rate limiting and caching. It includes secure email-based OTP (One-Time Password) verification for user authentication.

## Features

*   **User Management:** Secure user registration, login, and profile retrieval.
*   **OTP Verification:** Email-based One-Time Password (OTP) verification for enhanced security.
*   **JWT Authentication:** JSON Web Token (JWT) based access and refresh token authentication.
*   **Rate Limiting:** Protects against abuse and brute-force attacks using Redis.
*   **CORS:** Configurable Cross-Origin Resource Sharing.
*   **Logging:** Structured logging for better observability.
*   **Database:** PostgreSQL for reliable data storage.
*   **Asynchronous:** Built with FastAPI for high performance and asynchronous operations.

## Technologies

*   **Backend:** Python 3.10+, FastAPI
*   **Database:** PostgreSQL
*   **Caching/Messaging:** Redis
*   **Authentication:** JWT, Bcrypt (for password hashing), Email OTP
*   **Dependency Management:** `pip` / `requirements.txt`
*   **Code Quality:** `ruff`, `mypy` (recommended)

## Project Structure

```
python_project/
  authorization_service/
    api/                        # API endpoints and dependency injection
      v1/
        endpoints/              # Specific API routes (auth, users)
          auth.py
          users.py
        api.py                  # Main API router for v1
      deps.py                   # Dependency injection utilities
    core/                       # Core application configurations and utilities
      config.py                 # Pydantic settings management
      rate_limiter.py           # Rate limiting logic using Redis
      security.py               # Password hashing, JWT encoding/decoding
    db/                         # Database-related modules
      base.py                   # Base for SQLAlchemy models
      base_class.py             # Declarative base class
      session.py                # Database session management
    main.py                     # FastAPI application entry point
    models/                     # SQLAlchemy ORM models
      user.py                   # User model
    repositories/               # Data access layer
      user_repository.py        # Repository for user-related database operations
    schemas/                    # Pydantic models for request/response validation
      login.py                  # Login request/response schemas
      otp.py                    # OTP request/response schemas
      token.py                  # Token schemas
      user.py                   # User schemas
    services/                   # Business logic layer
      auth_service.py           # Authentication-related business logic
      minio_service.py          # Minio related business logic
      user_service.py           # User-related business logic
    utils/                      # Utility functions
      cors.py                   # CORS configuration
      email.py                  # Email sending utilities
      logger.py                 # Logging configuration
      otp.py                    # OTP generation and validation
  logs/                       # Application logs
  requirements.txt            # Python dependencies
  README.md                   # Project documentation
```

*   **REST base path:** `/api/v1`
*   **Resource naming:** Nouns in plural (`/users`)
*   **Packages and modules:** Use `snake_case`

## Setup

### Prerequisites

*   Python 3.10+
*   PostgreSQL database
*   Redis instance
*   `uvicorn` (will be installed with `requirements.txt`)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/gokulstabilix/fastapi_authorization.git
    ```

2.  **Create a virtual environment** (Windows PowerShell):

    ```powershell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```

    (Linux/macOS):

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**

    ```powershell
    pip install -r requirements.txt
    ```

### Configuration

1.  **Environment Variables:**
    Create a `.env` file in the `python_project/` directory (where `requirements.txt` is located) and populate it with the following variables. You can refer to `authorization_service/core/config.py` for default values and types.

    *   `PROJECT_NAME`: Name of your project (e.g., "Authorization Service")
    *   `API_V1_STR`: API version prefix (e.g., `/api/v1`)
    *   `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql+psycopg2://user:password@host:port/dbname`)
    *   `SECRET_KEY`: A strong, random string for JWT signing.
    *   `ALGORITHM`: JWT signing algorithm (e.g., `HS256`).
    *   `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration time for access tokens in minutes.
    *   `REFRESH_TOKEN_EXPIRE_DAYS`: Expiration time for refresh tokens in days.
    *   `BACKEND_CORS_ORIGINS`: Comma-separated list of allowed origins for CORS (e.g., `"http://localhost:3000,http://127.0.0.1:3000"`).
    *   `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_SSL`, `SMTP_USE_TLS`, `MAIL_FROM`: SMTP server settings for sending emails (e.g., for OTPs). `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM` are optional if email functionality is not required. `SMTP_PORT`, `SMTP_USE_SSL`, `SMTP_USE_TLS` have default values.
    *   `EMAIL_OTP_EXPIRE_MINUTES`: Expiration time for OTPs in minutes.
    *   `EMAIL_OTP_LENGTH`: Length of the generated OTP.
    *   `EMAIL_OTP_RESEND_INTERVAL_SECONDS`: Minimum time between OTP resend requests.
    *   `EMAIL_OTP_MAX_ATTEMPTS`: Maximum attempts to verify an OTP.
    *   `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`: Redis connection details.
    *   `RATE_LIMIT_LOGIN`, `RATE_LIMIT_REFRESH`, `RATE_LIMIT_SEND_OTP`, `RATE_LIMIT_VERIFY_OTP`, `RATE_LIMIT_DEFAULT`: Rate limiting rules (e.g., `"10/minute"`).
    *   `REDIS_CACHE_EXPIRE_SECONDS`: Expiration time for cached items in seconds.
    *   `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `DATABASE_POOL_TIMEOUT`, `DATABASE_POOL_RECYCLE`: SQLAlchemy database connection pooling settings.

2.  **Database Setup:**
    Ensure your PostgreSQL database is running and accessible via the `DATABASE_URL`. The application will automatically create necessary tables on startup if they don't exist.

### Running the Application

```powershell
uvicorn authorization_service.main:app  --reload
```

This will start the FastAPI application, typically accessible at `http://127.0.0.1:8000`. The `--reload` flag enables auto-reloading on code changes.

## API Endpoints

The API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs` .

### Authentication

*   **`POST /api/v1/users` - Create User**
    *   **Description:** Registers a new user with email, full name, and password.
    *   **Body:**
        ```json
        {
          "email": "jane.doe@example.com",
          "full_name": "Jane Doe",
          "password": "secret123"
        }
        ```

*   **`POST /api/v1/auth/send-otp` - Send Verification OTP**
    *   **Description:** Sends an OTP to the user's registered email for verification. Can be used to resend.
    *   **Body:**
        ```json
        { "email": "jane.doe@example.com" }
        ```

*   **`POST /api/v1/auth/verify-otp` - Verify OTP**
    *   **Description:** Verifies the provided OTP against the one sent to the user's email.
    *   **Body:**
        ```json
        { "email": "jane.doe@example.com", "otp": "123456" }
        ```

*   **`POST /api/v1/auth/login` - Login**
    *   **Description:** Authenticates a user and returns JWT access and refresh tokens.
    *   **Body:**
        ```json
        { "email": "jane.doe@example.com", "password": "secret123" }
        ```
    *   **Response:**
        ```json
        {
          "access_token": "<JWT>",
          "token_type": "bearer",
          "access_token_expires_in": 1800,
          "expires_at": "2025-01-01T12:34:56Z",
          "refresh_token": "<JWT>",
          "refresh_token_expires_in": 604800
        }
        ```

*   **`POST /api/v1/auth/refresh-token` - Refresh Access Token**
    *   **Description:** Uses a refresh token to obtain a new access token.
    *   **Body (plain string):** `<refresh_token_jwt>`
    *   **Response:** Same structure as login response, but without `refresh_token` fields.

*   **`GET /api/v1/users/profile` - Get Current User Profile (Protected)**
    *   **Description:** Retrieves the profile of the authenticated user. Requires a valid access token.
    *   **Header:** `Authorization: Bearer <JWT>`

## Notes

*   **Password Hashing:** Passwords are hashed using bcrypt via `passlib`.
*   **OTP Configuration:** OTP resend window, length, and maximum attempts are configurable via `.env` variables (`EMAIL_OTP_*`).
*   **Rate Limiting:** Configurable in `.env` (`RATE_LIMIT_*`).
*   **Logging:** Configured to output to `logs/app.log`.
*   **Nginx/Gunicorn:** For production deployment, it is recommended to run FastAPI with a production-ready ASGI server like Gunicorn and proxy it through Nginx.

## Contributing

@GokulG

## License

@GokulG
