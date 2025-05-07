from pathlib import Path
import shutil
import subprocess
import waqd

browser_proc = None


def start_web_server(reload=False):
    import uvicorn

    local_server_path = Path(__file__).parent / "local"
    shutil.copy(waqd.assets_path / "css" / "output.css", local_server_path)

    subprocess.Popen(
        "python -m http.server -b 127.0.0.1 8000",
        shell=True,
        cwd=str(local_server_path),
    )
    uvicorn.run(
        "waqd.ui.web2.main:web_app",
        host="0.0.0.0",  # localhost
        port=80,
        reload=reload,
        reload_excludes=["*.html", "*.css", ".log"],
    )


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
            "http://localhost:8000/login_admin.html",
            # "--force-device-scale-factor=0.8",
        ]
    )
