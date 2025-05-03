import waqd

browser_proc = None


def start_web_server(reload=False):
    import uvicorn

    uvicorn.run(
        "waqd.ui.web2.main:web_app",
        host="0.0.0.0",  # localhost
        port=8080,
        reload=reload,
        reload_excludes=["*.html", "*.css", ".log"],
    )


def start_web_browser():
    import webbrowser

    webbrowser.open("http://localhost:8080")


def start_web_ui_chromium_kiosk_mode():
    import subprocess

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
            "http://localhost:8080",
        ]
    )
