# Telegram FastAPI Frontend

React + Vite frontend для учебного Telegram Web clone.

## Auth endpoints

Фронт использует только новые явные сценарии:

- `POST /users/login/request-otp`
- `POST /users/login/verify-otp`
- `POST /users/register/request-otp`
- `POST /users/register/verify-otp`
- `POST /users/logout`

Старые `/users/request-otp` и `/users/verify-otp` удалены из backend, чтобы Swagger не путал вход и регистрацию.

## Seed media

`seed_data.py` генерирует реалистичные демо-медиа в `media/seed`:

- JPEG avatars/photos через `Pillow`
- MP4 story clips через `imageio` + `imageio-ffmpeg`

Зависимости зафиксированы в корневом `requirements.txt`.
