import waqd


def start_web_server(reload=False):
    import uvicorn

    uvicorn.run(
        "waqd.ui.web2.main:web_app",
        host="localhost",  # 0.0.0.0
        port=8080,
        # reload=reload,
        reload_excludes=[
            "*.html",
            "*.css",
        ],
    )


def start_web_ui():
    if waqd.DEBUG_LEVEL > 0:
        return
    import webbrowser

    webbrowser.open("http://localhost:8080")
