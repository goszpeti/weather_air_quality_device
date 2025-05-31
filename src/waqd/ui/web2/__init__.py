from datetime import timedelta
import os
from pathlib import Path
import shutil
import subprocess

import jwt
import waqd
from waqd.settings import USER_API_KEY, USER_DEFAULT_PW, USER_SESSION_SECRET
from .authentication import create_access_token
from .templates import base_template
import waqd.app as base_app

browser_proc = None
local_server = None
LOCAL_SERVER_PORT = "8080"


def start_web_server(reload=False):
    import uvicorn

    os.system("sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3.11")

    create_api_token()
    prepare_local_login()
    if reload:
        hostname = "localhost"
    else:
        hostname = "0.0.0.0"
    uvicorn.run(
        "waqd.ui.web2.main:web_app",
        host=hostname,
        port=80,
        reload=reload,
        reload_excludes=["*.html", "*.css", ".log"],
    )
    if browser_proc is not None:
        browser_proc.terminate()
    if local_server is not None:
        local_server.terminate()


def create_api_token():
    try:
        jwt.decode(
            base_app.settings.get_string(USER_API_KEY),
            base_app.settings.get_string(USER_SESSION_SECRET),
            algorithms=["HS256"],
        )
    except Exception:
        # Token is about to expire, create a new one
        base_app.settings.set(
            USER_API_KEY,
            create_access_token(
                {"sub": base_app.settings.get_string(USER_API_KEY)},
                expires_delta=timedelta(days=365),
            ),
        )
        base_app.settings.save()


def start_web_ui_chromium_kiosk_mode():
    # Start Chromium in kiosk mode
    global browser_proc
    browser_proc = subprocess.Popen(
        [
            "chromium-browser",
            "--kiosk",
            "--noerrdialogs",
            "--disable-infobars",
            "--disable-session-crashed-bubble",
            "--disable-restore-session-state",
            "--disable-translate",
            "--disable-pinch",
            "--disable-features=TranslateUI",
            f"http://localhost:{LOCAL_SERVER_PORT}/login_admin.html",
            "--force-device-scale-factor=0.8",
        ]
    )


def prepare_local_login():
    current_path = Path(__file__).parent.resolve()

    local_server_path = Path(__file__).parent / "local"
    shutil.copy(waqd.assets_path / "css" / "output.css", local_server_path)
    shutil.copy(waqd.assets_path / "font" / "Franzo-E4GA.woff", local_server_path)
    login_admin_file = "login_admin.html"
    login_admin_content = base_template(
        login_admin_file + ".in",
        {"password": base_app.settings.get_string(USER_DEFAULT_PW)},
        current_path / "local",
    )
    (current_path / "local" / login_admin_file).write_text(login_admin_content)

    global local_server
    local_server = subprocess.Popen(
        ["python", "-m", "http.server", "-b", "127.0.0.1", LOCAL_SERVER_PORT],
        cwd=str(local_server_path),
    )
