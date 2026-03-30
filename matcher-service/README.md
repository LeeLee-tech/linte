# Python Matcher Service

This service gives the Go backend an optional Python semantic matching backend.

## Run

```bash
cd Backend/matcher-service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Environment

```env
MATCHER_HOST=0.0.0.0
MATCHER_PORT=8010
MATCHER_USE_TRANSFORMER=1
MATCHER_MODEL_PATH=D:\models\bge-large-zh-v1.5
```

If the model cannot be loaded, the service falls back to a lightweight lexical matcher automatically.

## Go Backend Integration

Set this in `Backend/server-go/.env`:

```env
MATCHER_SERVICE_URL=http://127.0.0.1:8010
```
