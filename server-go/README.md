# Go Backend Rewrite

This directory contains a Gin-based rewrite of the original Python backend.

## Features

- JWT-based auth with real protected routes
- Registration, login, reset password, and email verification code flow
- User-isolated schedule CRUD
- Location update and nearby comprehensive match flow
- Lightweight Go matcher with a clean extension point for a future Python/LLM matcher service
- SQLite storage through GORM

## Run

```bash
cd Backend/server-go
go mod tidy
go run ./cmd/server
```

## Environment Variables

```env
APP_ENV=development
HOST=0.0.0.0
PORT=8000
DATABASE_URL=schedule.db
JWT_SECRET=change_me
JWT_EXPIRE_MINUTES=30
CODE_EXPIRE_MINUTES=5
CODE_SEND_COOLDOWN_SECONDS=60
NEARBY_ACTIVE_MINUTES=10
ALLOW_ORIGINS=*
MATCHER_SERVICE_URL=http://127.0.0.1:8010
MATCHER_AUTOSTART=true
MATCHER_MODEL_PATH=D:\models\bge-large-zh-v1.5

SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=
EXPOSE_DEBUG_CODE=true

QQ_EMAIL=
QQ_AUTH_CODE=
```

## API Notes

- Auth routes stay public under `/api/auth/*`
- `/api/schedule`, `/api/match`, `/api/user/update-location`, and `/api/match/find-nearby-comprehensive` require `Authorization: Bearer <token>`
- `user_id` is now derived from the JWT instead of trusting request bodies
- Schedule records now keep `title`, `date`, `time_range`, `location`, and `content`
- When SMTP is not configured and `EXPOSE_DEBUG_CODE=true`, `/api/auth/send-code` returns `debug_code` in the response for local integration testing
- `/api/auth/send-code` now applies a per-email cooldown and returns `429` with `retry_after_seconds` when requests are too frequent
