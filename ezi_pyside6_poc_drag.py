"""
ComfyUI-EZi - PySide6 Proof of Concept (WEB CHROME + DRAG)
Native title bar is hidden. The HTML bar is the only chrome.
Dragging the empty space in the HTML bar moves the window natively
(via Win32 WM_NCHITTEST simulation), so Windows snapping & FancyZones work.
"""

import sys
import os
import socket
import asyncio
import threading
import time
import ctypes
from ctypes import wintypes

# ---------------------------------------------------------------------------
# 0. Find your existing proxy port (or start a minimal one)
# ---------------------------------------------------------------------------

def find_free_port():
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]

# ---------------------------------------------------------------------------
# 1. Try to import PySide6
# ---------------------------------------------------------------------------

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QSizePolicy
    )
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import (
        QWebEnginePage, QWebEngineSettings, QWebEngineScript
    )
    from PySide6.QtCore import (
        Qt, QUrl, QSize, QPoint, QObject, Slot, QFile, QIODevice
    )
    from PySide6.QtGui import QIcon, QFont, QCursor
    PYSIDE6_AVAILABLE = True
except ImportError as e:
    print("=" * 60)
    print("PySide6 not installed!")
    print("Run: python_embeded\\python.exe -m pip install PySide6 aiohttp")
    print(f"Import error: {e}")
    print("=" * 60)
    PYSIDE6_AVAILABLE = False
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. Minimal proxy to serve your shell HTML
# ---------------------------------------------------------------------------

from aiohttp import web

async def make_test_app():
    async def handle_shell(request):
        return web.Response(text=TEST_HTML, content_type="text/html", charset="utf-8")

    app = web.Application()
    app.router.add_get("/", handle_shell)
    return app

def start_proxy(port):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        app = await make_test_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", port)
        await site.start()
        print(f"[Proxy] Serving test page at http://127.0.0.1:{port}/")
        await asyncio.Event().wait()

    loop.run_until_complete(run())

# ---------------------------------------------------------------------------
# 3. HTML Test Page (web-based title bar with drag support)
# ---------------------------------------------------------------------------

TEST_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ComfyUI-EZi - PySide6 Web Chrome + Drag</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0c0e12;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    color: #cccccc;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  #bar {
    display: flex;
    align-items: center;
    background: #161b22;
    border-bottom: 1px solid #21262d;
    padding: 0 10px;
    height: 32px;
    flex-shrink: 0;
    user-select: none;
    gap: 8px;
  }
  #dot { width: 8px; height: 8px; border-radius: 50%; background: #50fa7b; }
  #status { color: #8b949e; font-size: 11px; }
  .win-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 22px;
    padding: 0;
    font-family: inherit;
    font-size: 12px;
    font-weight: bold;
    border: 1px solid #30363d;
    border-radius: 4px;
    background: #21262d;
    color: #8b949e;
    cursor: pointer;
    box-sizing: border-box;
    line-height: 1;
    transition: all .15s;
  }
  .win-btn:hover {
    background: #0d419d;
    border-color: #58a6ff;
    color: #58a6ff;
  }
  .win-btn.danger:hover {
    background: #6e2020;
    border-color: #ff7070;
    color: #fff;
  }
  #drag-region {
    flex: 1 1 auto;
    align-self: stretch;
    min-width: 24px;
    margin: 0 8px;
    cursor: default;  /* show normal arrow, not text cursor */
  }
  #content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #8b949e;
    font-size: 14px;
  }
  .test-btn {
    padding: 8px 16px;
    margin: 4px;
    background: #21262d;
    border: 1px solid #388bfd;
    border-radius: 4px;
    color: #388bfd;
    cursor: pointer;
    font-family: inherit;
    font-size: 12px;
  }
  .test-btn:hover { background: #0d419d; }
</style>
</head>
<body>
<div id="bar">
  <div id="dot"></div>
  <span id="status">Web Chrome + Drag</span>
  <div id="drag-region" onmousedown="startWindowDrag()" title="Drag to move window"></div>
  <button class="win-btn" onclick="testBridge('minimize')" title="Minimize">&#8722;</button>
  <button class="win-btn" onclick="testBridge('maximize')" title="Maximize">&#9633;</button>
  <button class="win-btn danger" onclick="testBridge('close')" title="Close">&#10005;</button>
</div>
<div id="content">
  <div style="text-align:center">
    <div style="font-size:48px;margin-bottom:16px">&#128640;</div>
    <div style="color:#f1fa8c;font-size:16px;margin-bottom:8px">Web Chrome + Native Drag</div>
    <div style="color:#8b949e;margin-bottom:24px">Drag the empty bar space to move the window</div>
    <button class="test-btn" onclick="testBridge('minimize')">Test Minimize</button>
    <button class="test-btn" onclick="testBridge('maximize')">Test Maximize</button>
    <button class="test-btn" onclick="testBridge('close')">Test Close Confirm</button>
    <br><br>
    <div id="result" style="color:#50fa7b;font-size:11px;min-height:20px">Waiting for Qt bridge...</div>
  </div>
</div>
<script>
function testBridge(action) {
    var result = document.getElementById('result');
    result.textContent = 'Calling: ' + action + '...';

    if (window.qtBridge && window.qtBridge.handleAction) {
        window.qtBridge.handleAction(action);
        result.textContent = 'Sent: ' + action;
    } else if (window.pywebview && window.pywebview.api) {
        window.pywebview.api[action + '_window']();
        result.textContent = 'Sent (pywebview): ' + action;
    } else {
        result.textContent = 'ERROR: No bridge available!';
        console.error('No bridge available. qtBridge:', window.qtBridge, 'pywebview:', window.pywebview);
    }
}

function startWindowDrag() {
    if (window.qtBridge && window.qtBridge.startDrag) {
        window.qtBridge.startDrag();
    } else {
        console.warn("qtBridge.startDrag not available");
    }
}
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# 4. PySide6 Bridge Object
# ---------------------------------------------------------------------------

class QtBridge(QObject):
    """Bridge for Python-JS communication + native window drag."""

    def __init__(self, window):
        super().__init__()
        self._window = window
        self._is_maximized = False

    @Slot(str)
    def handleAction(self, action):
        """Called from JavaScript via QWebChannel."""
        print(f"[Bridge] Received action: {action}")

        if action == "minimize":
            self._window.showMinimized()
            print(f"[Bridge] showMinimized() called. isMinimized={self._window.isMinimized()}")

        elif action == "maximize":
            if self._window.isMaximized():
                self._window.showNormal()
                self._is_maximized = False
                print(f"[Bridge] showNormal() called")
            else:
                self._window.showMaximized()
                self._is_maximized = True
                print(f"[Bridge] showMaximized() called. isMaximized={self._window.isMaximized()}")

        elif action == "close":
            self._confirm_close()

    @Slot()
    def startDrag(self):
        """Initiate native window drag from HTML drag region.

        Uses Win32 SendMessage with WM_NCLBUTTONDOWN + HTCAPTION.
        This gives native Windows behavior: snapping, FancyZones, etc.
        """
        try:
            hwnd = int(self._window.winId())
            user32 = ctypes.windll.user32

            # Release capture from whichever window has it (usually the web view)
            user32.ReleaseCapture()

            # Get current cursor position for the message
            cursor = QCursor.pos()
            x = cursor.x() & 0xFFFF
            y = cursor.y() & 0xFFFF
            lparam = (y << 16) | x

            # WM_NCLBUTTONDOWN = 0xA1, HTCAPTION = 2
            user32.SendMessageW(hwnd, 0xA1, 2, lparam)
            print(f"[Bridge] startDrag() -> SendMessage WM_NCLBUTTONDOWN at ({cursor.x()}, {cursor.y()})")
        except Exception as e:
            print(f"[Bridge] startDrag() failed: {e}")

    def _confirm_close(self):
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self._window,
            "Close ComfyUI?",
            "ComfyUI will be stopped and the window will close.\n\nDo you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            print("[Bridge] User confirmed close")
            self._window.close()
        else:
            print("[Bridge] User cancelled close")

# ---------------------------------------------------------------------------
# 5. Main Window (NO native title bar — web chrome only)
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, proxy_port):
        super().__init__()
        self.proxy_port = proxy_port
        self._setup_ui()

    def _setup_ui(self):
        # Frameless window — NO native title bar
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.resize(1200, 800)
        self.setMinimumSize(400, 300)

        # Central widget with vertical layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Web view fills ENTIRE window (web-based chrome inside HTML)
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Configure web engine
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)

        # Setup bridge and inject QWebChannel scripts BEFORE loading page
        self._setup_bridge()

        # Load page (includes web-based title bar with drag region)
        self.web_view.load(QUrl(f"http://127.0.0.1:{self.proxy_port}/"))
        layout.addWidget(self.web_view)

    def _setup_bridge(self):
        """Setup QWebChannel for Python-JS communication."""
        try:
            from PySide6.QtWebChannel import QWebChannel

            self.bridge = QtBridge(self)
            self.channel = QWebChannel()
            self.channel.registerObject("qtBridge", self.bridge)
            self.web_view.page().setWebChannel(self.channel)

            # Inject qwebchannel.js and bridge initialization
            self._inject_webchannel_scripts()
            print("[MainWindow] QWebChannel bridge setup complete")

        except ImportError:
            print("[MainWindow] QWebChannel not available, using fallback")
            self.bridge = QtBridge(self)

    def _inject_webchannel_scripts(self):
        """Inject Qt's qwebchannel.js and bridge initializer into the page."""
        page = self.web_view.page()

        # 1. Inject Qt's QWebChannel JS library
        js_file = QFile(":/qtwebchannel/qwebchannel.js")
        if js_file.open(QIODevice.ReadOnly):
            qwebchannel_js = bytes(js_file.readAll()).decode("utf-8")
            js_file.close()

            lib_script = QWebEngineScript()
            lib_script.setName("qwebchannel.lib")
            lib_script.setSourceCode(qwebchannel_js)
            lib_script.setInjectionPoint(QWebEngineScript.DocumentCreation)
            lib_script.setWorldId(QWebEngineScript.MainWorld)
            lib_script.setRunsOnSubFrames(True)
            page.scripts().insert(lib_script)
        else:
            print("[Inject] WARNING: Could not load :/qtwebchannel/qwebchannel.js")
            js_file.close()

        # 2. Inject bridge initialization (connects window.qtBridge)
        init_js = """
        (function() {
            if (typeof qt === 'undefined' || !qt.webChannelTransport) {
                console.warn("qt.webChannelTransport not available yet");
                return;
            }
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.qtBridge = channel.objects.qtBridge;
                console.log("Qt bridge initialized via QWebEngineScript");
                var result = document.getElementById('result');
                if (result) result.textContent = "Qt bridge connected! Drag the bar empty space to move.";
            });
        })();
        """
        init_script = QWebEngineScript()
        init_script.setName("qwebchannel.init")
        init_script.setSourceCode(init_js)
        init_script.setInjectionPoint(QWebEngineScript.DocumentReady)
        init_script.setWorldId(QWebEngineScript.MainWorld)
        init_script.setRunsOnSubFrames(True)
        page.scripts().insert(init_script)

    def showEvent(self, event):
        super().showEvent(event)
        print(f"[Window] Shown: size={self.size()}, pos={self.pos()}")
        print(f"[Window] isMaximized={self.isMaximized()}, isMinimized={self.isMinimized()}")

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            state = self.windowState()
            print(f"[Window] State changed: {state}")
            print(f"[Window] isMaximized={self.isMaximized()}, isMinimized={self.isMinimized()}")
        super().changeEvent(event)

    def closeEvent(self, event):
        print("[Window] closeEvent triggered")
        event.accept()

    def showMinimized(self):
        print("[Window] showMinimized() called")
        super().showMinimized()

    def showMaximized(self):
        print("[Window] showMaximized() called")
        super().showMaximized()

    def showNormal(self):
        print("[Window] showNormal() called")
        super().showNormal()

# ---------------------------------------------------------------------------
# 6. Main Entry Point
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("ComfyUI-EZi - PySide6 Web Chrome + Native Drag Test")
    print("=" * 60)

    # Start proxy
    proxy_port = find_free_port()
    proxy_thread = threading.Thread(target=start_proxy, args=(proxy_port,), daemon=True)
    proxy_thread.start()
    time.sleep(1)

    # Create Qt app
    app = QApplication(sys.argv)
    app.setApplicationName("ComfyUI-EZi-Qt-WebChrome")
    app.setApplicationDisplayName("ComfyUI-EZi Desktop")

    # Create main window
    window = MainWindow(proxy_port)
    window.show()

    print(f"\n[Main] Window shown with WEB CHROME + DRAG.")
    print(f"  - HTML title bar is the ONLY chrome visible.")
    print(f"  - Click buttons (minimize, maximize, close) -> bridge actions.")
    print(f"  - Click+drag the EMPTY space in the bar -> native window drag.")
    print(f"  - Window snapping (Win+arrows, drag to screen edge) should work.")
    print(f"  - FancyZones / PowerToys snap should work during drag.")
    print(f"\n[Main] Close window or press Ctrl+C to exit\n")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()