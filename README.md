# Medication Reminder

A FastAPI + React medication reminder for one patient. It sends Bark notifications on a schedule, provides a patient pill sheet, and includes a password-protected admin dashboard.

## Stack

- FastAPI, SQLAlchemy, MySQL, APScheduler
- React, TypeScript, Vite, Material UI
- Bark push notifications
- Asia/Tokyo scheduling by default

## Safe setup on a new server

### 1. Install prerequisites

Use a Linux server with Python 3.11+, Node.js 20+, npm, and MySQL 8+. Keep MySQL bound to localhost or a private network; do not expose port 3306 to the internet.

```bash
git clone https://github.com/sobanbackup1/medicine-reminder.git
cd medicine-reminder
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm ci
```

### 2. Create a private environment file

```bash
cp .env.example .env
chmod 600 .env
```

Generate a unique JWT secret and a strong admin password. Never commit `.env`.

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Edit `.env` and set at least `MYSQL_PASSWORD`, `SECRET_KEY`, `ADMIN_PASSWORD`, `WEBSITE_URL`, `PATIENT_BARK_KEY`, and `EMERGENCY_BARK_KEY`. Use an HTTPS URL for `WEBSITE_URL`.

Use the Bark device key for the patient and the separate emergency-contact device key. Do not paste keys into GitHub issues, README files, logs, or chat.

### 3. Create a dedicated MySQL database user

Run as a MySQL administrator, replacing the password with the value from `.env`:

```sql
CREATE DATABASE medication_reminder CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'medication'@'localhost' IDENTIFIED BY 'strong-database-password';
GRANT ALL PRIVILEGES ON medication_reminder.* TO 'medication'@'localhost';
FLUSH PRIVILEGES;
```

Set the same database name, user, and password in `.env`.

### 4. Build and run

```bash
npm run build
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The application creates its tables on startup. Put it behind an HTTPS reverse proxy or a Cloudflare Tunnel. Do not expose Uvicorn directly to the internet.

For production, run Uvicorn with a systemd service and set `Restart=always`. Keep the service user limited to the application and backup directories.

## Notification behavior

The scheduler uses `TIMEZONE` and these settings:

- `REMINDER_START_TIME`: first patient reminder
- `REMINDER_INTERVAL`: minutes between reminders
- `EMERGENCY_TIME`: emergency-contact notification if the patient is still pending
- midnight: stops the previous reminder cycle and opens the new day as `pending`

The system does not automatically mark a dose as missed. The patient must press the Japanese `飲み忘れ` button. Reminders stop after `taken`, `forgot`, or `missed`.

The emergency notification is sent only while the day is still `pending`.

## Admin dashboard

Open `/admin` on the configured HTTPS site and sign in with `ADMIN_PASSWORD`.

The dashboard provides today’s status, calendar, statistics, notification logs, settings, backups, and CSV export. Secret settings are not returned to the browser; leave a secret field blank to keep its current value.

## Backups and recovery

Keep the `backups/` directory outside Git and restrict it to the service account. Create backups from the admin page or the server backup process. Restore only after stopping the application and verifying the backup file:

```bash
mysql -u medication -p medication_reminder < backups/backup.sql
```

Restart the service and check `/api/health` afterward.

## Security checklist

- Use HTTPS and a valid certificate.
- Use unique `SECRET_KEY`, admin password, database password, and Bark keys.
- Never commit `.env`, SQL dumps, logs, `.venv`, `node_modules`, or `dist`.
- Restrict MySQL and the Uvicorn port to localhost/private networking.
- Rotate Bark keys and admin/database credentials if they are ever exposed.
- Review notification and event logs after deployment.
