# Morang Model College & School Website

Premium educational website – **Structured & Powered by [BAM Studio](https://www.arganbhujel.info.np/)**

## Local run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

- Site: http://127.0.0.1:5000  
- Admin: http://127.0.0.1:5000/admin (`admin` / `admin123`)

## Deploy on Vercel

1. Push this project to GitHub.
2. Import the repo in [Vercel](https://vercel.com).
3. **Framework Preset:** Other  
4. **Build Command:** leave empty (or `pip install -r requirements.txt`)  
5. **Output:** not required (serverless via `api/index.py`)
6. Add **Environment Variables** in Vercel:

| Name | Value |
|------|--------|
| `SECRET_KEY` | long random string |
| `DATABASE_URL` | PostgreSQL URL (Neon / Supabase / Vercel Postgres) |
| `ADMIN_USERNAME` | admin |
| `ADMIN_PASSWORD` | your-secure-password |
| `MAIL_SERVER` | smtp.gmail.com |
| `MAIL_PORT` | 587 |
| `MAIL_USE_TLS` | True |
| `MAIL_USERNAME` | your email |
| `MAIL_PASSWORD` | app password |
| `CLOUDINARY_URL` | optional, for file uploads |

7. Deploy.

**Important for Vercel**
- Use **PostgreSQL** (`DATABASE_URL`) — SQLite does not persist on serverless.
- For image/file uploads, configure **Cloudinary** (`CLOUDINARY_URL`).
- Static files are routed via `vercel.json`.

## Contact / Studio

**BAM Studio**  
Website & contact: [https://www.arganbhujel.info.np/](https://www.arganbhujel.info.np/)

## Stack

Flask · SQLAlchemy · Jinja2 · Flask-Login · Flask-Mail · Glass/Neon UI
