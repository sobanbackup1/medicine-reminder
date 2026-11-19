#!/usr/bin/env python3
"""One-command bootstrap and launcher.

Running `python run.py` will:

  1. Create a Python virtual environment if needed
  2. Install Python dependencies
  3. Install frontend dependencies and build the React app
  4. Ensure MySQL is installed and running (install if possible)
  5. Create the MySQL database and user if needed
  6. Create all database tables
  7. Start the FastAPI backend (which starts the scheduler and serves
     the built frontend)

No manual database setup is required.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"

IS_WINDOWS = sys.platform.startswith("win")
VENV_PYTHON = VENV_DIR / ("Scripts" if IS_WINDOWS else "bin") / "python"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def run(cmd: list[str], **kw) -> int:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.call(cmd, **kw)


def which(name: str) -> bool:
    return shutil.which(name) is not None


def ensure_env_file():
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            shutil.copy(ENV_EXAMPLE, ENV_FILE)
            print("Created .env from .env.example — edit it with your Bark keys and MySQL password.")
        else:
            print("WARNING: no .env file found and no .env.example to copy from.")


# --------------------------------------------------------------------------- #
# Python venv + deps
# --------------------------------------------------------------------------- #
def ensure_venv():
    if VENV_PYTHON.exists():
        return
    print("Creating Python virtual environment...")
    venv.create(VENV_DIR, with_pip=True, clear=False)
    run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"])


def install_python_deps():
    print("Installing Python dependencies...")
    run([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS)])


# --------------------------------------------------------------------------- #
# Frontend
# --------------------------------------------------------------------------- #
def ensure_node():
    if which("node") and which("npm"):
        return True
    print("Node.js / npm not found.")
    if IS_WINDOWS:
        print("Please install Node.js from https://nodejs.org/ and re-run.")
        return False
    # Try nvm or apt
    if which("apt-get"):
        print("Attempting to install Node.js via apt...")
        run(["apt-get", "update", "-y"])
        run(["apt-get", "install", "-y", "nodejs", "npm"])
        return which("node") and which("npm")
    if which("nvm"):
        run(["nvm", "install", "--lts"])
        return which("node") and which("npm")
    print("Could not install Node.js automatically. Please install it from https://nodejs.org/")
    return False


def build_frontend():
    if not (PROJECT_ROOT / "package.json").exists():
        print("No package.json found — skipping frontend build.")
        return
    if not ensure_node():
        print("ERROR: Node.js is required to build the frontend.")
        sys.exit(1)

    print("Installing frontend dependencies...")
    run(["npm", "install"], cwd=str(PROJECT_ROOT))

    print("Building frontend...")
    run(["npm", "run", "build"], cwd=str(PROJECT_ROOT))


# --------------------------------------------------------------------------- #
# MySQL
# --------------------------------------------------------------------------- #
def ensure_mysql():
    if which("mysql"):
        return True
    print("MySQL client not found.")
    if IS_WINDOWS:
        print("Please install MySQL from https://dev.mysql.com/downloads/ and re-run.")
        return False
    if which("apt-get"):
        print("Attempting to install MySQL via apt...")
        run(["apt-get", "update", "-y"])
        run(["apt-get", "install", "-y", "mysql-server", "mysql-client"])
        # start the service
        run(["", "systemctl", "start", "mysql"], cwd=None)
        return which("mysql")
    print("Could not install MySQL automatically. Please install MySQL manually.")
    return False


def ensure_mysql_db():
    """Create the database and user if they don't exist."""
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "medication")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "medication_reminder")

    root_user = "root"
    if not password:
        print("MYSQL_PASSWORD must be set before creating the database user.")
        return

    def sql_literal(value: str) -> str:
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"

    db_user_host = "localhost" if host in {"localhost", "127.0.0.1"} else host
    account = f"{sql_literal(user)}@{sql_literal(db_user_host)}"
    sql = (
        f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        f" CREATE USER IF NOT EXISTS {account} IDENTIFIED BY {sql_literal(password)};"
        f" GRANT ALL PRIVILEGES ON `{database}`.* TO {account};"
        " FLUSH PRIVILEGES;"
    )

    mysql_env = os.environ.copy()
    root_password = os.getenv("MYSQL_ROOT_PASSWORD")
    if root_password:
        mysql_env["MYSQL_PWD"] = root_password
    ret = subprocess.run(
        ["mysql", "-u", root_user, f"-h{host}", f"-P{port}"],
        input=sql,
        text=True,
        env=mysql_env,
    ).returncode
    if ret == 0:
        print(f"Database '{database}' and user are ready.")
    else:
        print("Could not create the MySQL database automatically. Create it manually as a MySQL administrator.")


# --------------------------------------------------------------------------- #
# Start backend
# --------------------------------------------------------------------------- #
def start_server():
    print("Starting FastAPI backend...")
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = os.getenv("APP_PORT", "8000")
    run([
        str(VENV_PYTHON), "-m", "uvicorn",
        "backend.main:app",
        "--host", host,
        "--port", str(port),
    ], cwd=str(PROJECT_ROOT))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ensure_env_file()
    ensure_venv()
    install_python_deps()
    build_frontend()
    if not ensure_mysql():
        print("ERROR: MySQL is required. Install it and re-run.")
        sys.exit(1)
    ensure_mysql_db()
    start_server()


if __name__ == "__main__":
    main()
