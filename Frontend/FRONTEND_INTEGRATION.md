# Frontend Integration Guide

This document describes how the frontend should integrate with the current Go backend.

Backend root:

- `http://127.0.0.1:8000`

Health check:

- `GET /health`

## Auth Flow

The backend uses JWT bearer tokens.

After login or successful registration, store:

- `access_token`
- `user_id`
- `email`

For protected APIs, send:

```http
Authorization: Bearer <access_token>
```

## Environment Notes

The backend supports two verification code modes:

1. Real SMTP mode
   When SMTP is configured, `/api/auth/send-code` sends a real email.

2. Debug mode
   When SMTP is not configured and `EXPOSE_DEBUG_CODE=true`, `/api/auth/send-code` returns `debug_code` in the response.

This is useful for local frontend-backend integration without email setup.

## Auth APIs

### Send Verification Code

`POST /api/auth/send-code`

Request:

```json
{
  "email": "user@example.com",
  "type": "register"
}
```

`type` allowed values:

- `register`
- `reset`

Success response in SMTP mode:

```json
{
  "msg": "verification code generated"
}
```

Success response in debug mode:

```json
{
  "msg": "verification code generated in debug mode",
  "debug_code": "123456"
}
```

Rate limit response:

Status: `429`

```json
{
  "error": "verification code requested too frequently",
  "retry_after_seconds": 42
}
```

Mailer failure response:

Status: `503`

```json
{
  "error": "failed to send verification email"
}
```

Frontend handling suggestion:

- If `debug_code` exists, show it in development UI or console for easy testing.
- If `429`, show a countdown or tell the user to retry after `retry_after_seconds`.

### Register

`POST /api/auth/register`

Request:

```json
{
  "email": "user@example.com",
  "password": "123456",
  "code": "123456"
}
```

Success response:

```json
{
  "user_id": "user_xxx",
  "email": "user@example.com",
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### Login

`POST /api/auth/login`

Request:

```json
{
  "email": "user@example.com",
  "password": "123456"
}
```

Success response:

```json
{
  "user_id": "user_xxx",
  "email": "user@example.com",
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Failure response:

Status: `401`

```json
{
  "error": "invalid email or password"
}
```

### Reset Password

`POST /api/auth/reset-password`

Request:

```json
{
  "email": "user@example.com",
  "new_password": "newpass123",
  "code": "123456"
}
```

Success response:

```json
{
  "msg": "password reset successful"
}
```

## Schedule APIs

All schedule APIs require bearer token.

### List Schedules

`GET /api/schedule`

Success response:

```json
[
  {
    "id": "sched_xxx",
    "user_id": "user_xxx",
    "title": "Study",
    "date": "2026-03-30",
    "time_range": "14:00-16:00",
    "location": "Library",
    "content": "Study Library",
    "created_at": "2026-03-30T10:00:00Z",
    "updated_at": "2026-03-30T10:00:00Z"
  }
]
```

Frontend display mapping:

- `title` -> title
- `date` -> date
- `time_range` -> split into `startTime` and `endTime`
- `location` -> location
- `content` -> optional detail text

### Create Schedule

`POST /api/schedule`

Request:

```json
{
  "title": "Study",
  "date": "2026-03-30",
  "time_range": "14:00-16:00",
  "location": "Library",
  "content": "Study Library"
}
```

Success response returns the created schedule object.

### Update Schedule

`PUT /api/schedule/:schedule_id`

Request body is the same as create.

Success response returns the updated schedule object.

### Delete Schedule

`DELETE /api/schedule/:schedule_id`

Success response:

```json
{
  "msg": "delete successful"
}
```

## Match APIs

All match APIs require bearer token.

### Basic Match

`POST /api/match`

Request:

```json
{
  "my_profile": {
    "id": "self_1",
    "title": "Need a frontend partner",
    "time_range": "14:00-16:00",
    "content": "Looking for someone familiar with Vue and API integration"
  },
  "candidates": [
    {
      "id": "c1",
      "title": "Frontend engineer",
      "time_range": "14:30-15:30",
      "content": "Good at Vue and React"
    }
  ]
}
```

Success response:

```json
{
  "matches": [
    {
      "id": "c1",
      "time": "14:30-15:30",
      "content": "Good at Vue and React",
      "score": 0.88,
      "level": "high"
    }
  ]
}
```

### Update Location

`POST /api/user/update-location`

Request:

```json
{
  "latitude": 31.2304,
  "longitude": 121.4737
}
```

Success response:

```json
{
  "msg": "location updated",
  "time": "2026-03-30T10:00:00Z"
}
```

### Nearby Comprehensive Match

`POST /api/match/find-nearby-comprehensive`

Request:

```json
{
  "latitude": 31.2304,
  "longitude": 121.4737,
  "radius_meters": 200,
  "my_schedules": [
    {
      "id": "self_sched_1",
      "title": "Study",
      "time_range": "14:00-16:00",
      "content": "Looking for someone to study with"
    }
  ]
}
```

Success response with matches:

```json
{
  "msg": "matching completed",
  "total_nearby_users": 3,
  "matches": [
    {
      "target_user_id": "user_abc",
      "target_email": "target@example.com",
      "distance_m": 88.6,
      "my_schedule_title": "Study",
      "matched_schedule_id": "sched_123",
      "matched_time": "14:30-15:30",
      "matched_content": "Available to study together",
      "score": 0.81,
      "score_level": "high"
    }
  ]
}
```

Success response with no nearby users:

```json
{
  "msg": "no active nearby users found",
  "total_nearby_users": 0,
  "matches": []
}
```

## Current Frontend Behavior

The current page already supports:

- Backend base URL input in settings
- Register
- Login
- Reset password
- Local schedule mode when not logged in
- Cloud schedule sync when logged in

Implementation entry:

- [script.js](/C:/Users/20162/Desktop/comdes/Linte-main/Frontend/script.js)

## Recommended Frontend Handling

1. Always centralize requests through one helper that adds bearer token automatically.
2. After login/register success, immediately store `access_token` and refresh schedules.
3. For send-code:
   - show `debug_code` in development
   - show cooldown message on `429`
   - show service warning on `503`
4. For schedule rendering, normalize `time_range` into `startTime` and `endTime`.

## Quick Test Sequence

1. Set backend base URL to `http://127.0.0.1:8000`
2. Send register code
3. If backend is in debug mode, use returned `debug_code`
4. Register and store JWT
5. Create a schedule
6. Refresh schedule list
7. Update and delete the schedule

## Common Issues

- `401 unauthorized`
  Usually missing or expired bearer token.

- `429 too many requests`
  Wait `retry_after_seconds` before requesting another code.

- `503 failed to send verification email`
  SMTP is configured incorrectly or email service is unavailable.

- No `debug_code` in response
  Backend is likely running with SMTP configured or `EXPOSE_DEBUG_CODE=false`.
