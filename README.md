# Authorization_service (FastAPI + Postgres)

Enterprise-grade structure with versioned REST APIs and Postgres persistence for users. Includes email-based OTP verification.

## Structure

```
python_project/
  authorization_service/
    api/
      v1/
        endpoints/
          users.py
        api.py
      __init__.py
      deps.py
    core/
      config.py
      __init__.py
    crud/
      user.py
      __init__.py
    db/
      base.py
      base_class.py
      session.py
      __init__.py
    models/
      user.py
      __init__.py
    schemas/
      user.py
      otp.py
      __init__.py
    __init__.py
    main.py
  __init__.py
  .env.example
  requirements.txt
  README.md
```

- REST base path: `/api/v1`
- Resource naming: nouns in plural (`/users`)
- Packages and modules use `snake_case`

## Setup

1. Create a virtual environment (Windows PowerShell):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
2. Install dependencies:
   ```powershell
   pip install -r python_project/requirements.txt
   ```
3. Configure environment:
    - Copy `python_project/.env.example` to `python_project/.env`
    - Update `DATABASE_URL` for your Postgres instance
    - Configure SMTP (mapped from typical Spring config):
      - `SMTP_HOST=mail.stabilix.com`
      - `SMTP_PORT=465`
      - `SMTP_USERNAME=mailsrv1@stabilix.com`
      - `SMTP_PASSWORD=***` (do not commit real passwords)
      - `SMTP_USE_SSL=true`
      - `SMTP_USE_TLS=false`
   - Ensure the database exists (e.g., `python_project`)
4. Run the API:
   ```powershell
   uvicorn python_project.authorization_service.main:app --reload
   ```

## OTP/Email Verification Flow
## API

- Create user
  - Method: `POST`
  - Path: `/api/v1/users`
  - Body:
    ```json
    {
      "email": "jane.doe@example.com",
      "full_name": "Jane Doe",
      "password": "secret123"
    }
    ```
- Send verification OTP (resend)
  - Method: `POST`
  - Path: `/api/v1/auth/send-otp`
  - Body:
    ```json
    { "email": "jane.doe@example.com" }
    ```

- Verify OTP
  - Method: `POST`
  - Path: `/api/v1/auth/verify-otp`
  - Body:
    ```json
    { "email": "jane.doe@example.com", "otp": "123456" }
    ```

- Login (get JWT access and refresh tokens)
  - Method: `POST`
  - Path: `/api/v1/auth/login`
  - Body (JSON):
    ```json
    { "email": "jane.doe@example.com", "password": "secret123" }
    ```
  - Response:
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

- Refresh access token
  - Method: `POST`
  - Path: `/api/v1/auth/refresh-token`
  - Body (plain string): `refresh_token`
  - Response: same structure as access token without refresh fields.
- Get current user (protected)
  - Method: `GET`
  - Path: `/api/v1/users/profile`
  - Header: `Authorization: Bearer <JWT>`

- Docs: `http://127.0.0.1:8000/docs`

## Notes

- Tables are auto-created on startup via `Base.metadata.create_all`. For existing databases, new columns for OTP verification must be added via migration. Example (PostgreSQL):
  ```sql
  ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_email_verified boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS email_otp_hash varchar(255),
    ADD COLUMN IF NOT EXISTS email_otp_expires_at timestamptz,
    ADD COLUMN IF NOT EXISTS email_otp_attempts integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS email_otp_last_sent_at timestamptz;
  ```
- Passwords are hashed using bcrypt via `passlib`.
- OTP resend window and limits are configurable via `.env` (`EMAIL_OTP_*`).
- Naming conventions and layout follow common enterprise patterns for FastAPI projects.
