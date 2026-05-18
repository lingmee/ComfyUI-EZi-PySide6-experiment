"""
ComfyUI-EZi - PySide6 Proof of Concept
Minimal test to verify frameless window behavior before full port.

This loads your existing HTML shell through your existing aiohttp proxy.
"""

import sys
import os
import subprocess
import socket
import asyncio
import threading
import json
import time

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
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    from PySide6.QtCore import Qt, QUrl, QSize, QPoint, QObject
    from PySide6.QtGui import QIcon, QFont, QCursor
    PYSIDE6_AVAILABLE = True
except ImportError:
    print("=" * 60)
    print("PySide6 not installed!")
    print("Run: python_embeded\\python.exe -m pip install PySide6 PySide6-WebEngine")
    print("=" * 60)
    PYSIDE6_AVAILABLE = False
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. Minimal proxy to serve your shell HTML
# ---------------------------------------------------------------------------

# Copy your shell HTML here, or we'll load from file
# For this POC, we'll create a simple test page that mimics your bar

TEST_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ComfyUI-EZi - PySide6 Test</title>
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
    -webkit-app-region: drag;
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
    -webkit-app-region: no-drag;
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
    -webkit-app-region: drag;
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
  <span id="status">PySide6 Test Mode</span>
  <div id="drag-region"></div>
  <button class="win-btn" onclick="testBridge('minimize')" title="Minimize">&#8722;</button>
  <button class="win-btn" onclick="testBridge('maximize')" title="Maximize">&#9633;</button>
  <button class="win-btn danger" onclick="testBridge('close')" title="Close">&#10005;</button>
</div>
<div id="content">
  <div style="text-align:center">
    <div style="font-size:48px;margin-bottom:16px">&#128640;</div>
    <div style="color:#f1fa8c;font-size:16px;margin-bottom:8px">PySide6 Proof of Concept</div>
    <div style="color:#8b949e;margin-bottom:24px">Testing frameless window behavior</div>
    <button class="test-btn" onclick="testBridge('minimize')">Test Minimize</button>
    <button class="test-btn" onclick="testBridge('maximize')">Test Maximize</button>
    <button class="test-btn" onclick="testBridge('close')">Test Close Confirm</button>
    <br><br>
    <div id="result" style="color:#50fa7b;font-size:11px;min-height:20px"></div>
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

// Expose bridge object for Qt
if (typeof qtBridge === 'undefined') {
    window.qtBridge = {
        handleAction: function(action) {
            console.log('qtBridge received:', action);
        }
    };
}
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# 3. Start minimal HTTP server
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
# 4. PySide6 Bridge Object (replaces your Api class)
# ---------------------------------------------------------------------------

class QtBridge(QObject):
    """Minimal bridge to test Python-JS communication."""

    def __init__(self, window):
        super().__init__()
        self._window = window
        self._is_maximized = False

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
# 5. Custom Title Bar (optional - for testing native Qt chrome)
# ---------------------------------------------------------------------------

class CustomTitleBar(QWidget):
    """Native Qt title bar with working buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self._drag_pos = None

        self.setFixedHeight(32)
        self.setStyleSheet("""
            QWidget {
                background: #161b22;
                border-bottom: 1px solid #21262d;
            }
            QPushButton {
                width: 28px;
                height: 22px;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #30363d;
                border-radius: 4px;
                background: #21262d;
                color: #8b949e;
            }
            QPushButton:hover {
                background: #0d419d;
                border-color: #58a6ff;
                color: #58a6ff;
            }
            QPushButton#closeBtn:hover {
                background: #6e2020;
                border-color: #ff7070;
                color: #fff;
            }
            QLabel {
                color: #8b949e;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        # Status dot
        self.dot = QLabel("●")
        self.dot.setStyleSheet("color: #50fa7b; font-size: 10px;")
        layout.addWidget(self.dot)

        # Status text
        self.status = QLabel("Qt Native Title Bar")
        layout.addWidget(self.status)

        # Drag region (spacer)
        layout.addStretch()

        # Window buttons
        self.btn_min = QPushButton("−")
        self.btn_min.setToolTip("Minimize")
        self.btn_min.clicked.connect(self._on_minimize)

        self.btn_max = QPushButton("□")
        self.btn_max.setToolTip("Maximize / Restore")
        self.btn_max.clicked.connect(self._on_maximize)

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Close")
        self.btn_close.setObjectName("closeBtn")
        self.btn_close.clicked.connect(self._on_close)

        for btn in [self.btn_min, self.btn_max, self.btn_close]:
            btn.setFixedSize(28, 22)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            layout.addWidget(btn)

    def _on_minimize(self):
        print("[QtTitleBar] Minimize clicked")
        if self._parent:
            self._parent.showMinimized()
            print(f"[QtTitleBar] isMinimized={self._parent.isMinimized()}")

    def _on_maximize(self):
        print("[QtTitleBar] Maximize clicked")
        if self._parent:
            if self._parent.isMaximized():
                self._parent.showNormal()
                self.btn_max.setText("□")
                print("[QtTitleBar] showNormal()")
            else:
                self._parent.showMaximized()
                self.btn_max.setText("❐")
                print(f"[QtTitleBar] showMaximized(), isMaximized={self._parent.isMaximized()}")

    def _on_close(self):
        print("[QtTitleBar] Close clicked")
        if self._parent:
            self._parent.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self._parent.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

# ---------------------------------------------------------------------------
# 6. Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, proxy_port):
        super().__init__()
        self.proxy_port = proxy_port
        self._setup_ui()

    def _setup_ui(self):
        # Frameless window
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

        # --- OPTION A: Native Qt title bar (recommended for testing) ---
        self.title_bar = CustomTitleBar(self)
        layout.addWidget(self.title_bar)

        # --- OPTION B: Web-based title bar (your current approach) ---
        # Uncomment below and comment out the CustomTitleBar to test web-based chrome
        # self.web_view = QWebEngineView()
        # self.web_view.load(QUrl(f"http://127.0.0.1:{self.proxy_port}/"))
        # layout.addWidget(self.web_view)
        # return  # Skip the rest if using web-based

        # Web view below title bar
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Configure web engine
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)

        # Setup bridge
        self._setup_bridge()

        # Load page
        self.web_view.load(QUrl(f"http://127.0.0.1:{self.proxy_port}/"))
        layout.addWidget(self.web_view)

        # Window state tracking
        self._restore_rect = None

    def _setup_bridge(self):
        """Setup QWebChannel for Python-JS communication."""
        try:
            from PySide6.QtWebChannel import QWebChannel

            self.bridge = QtBridge(self)
            self.channel = QWebChannel()
            self.channel.registerObject("qtBridge", self.bridge)
            self.web_view.page().setWebChannel(self.channel)

            # Inject bridge script
            script = """
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.qtBridge = channel.objects.qtBridge;
                console.log("Qt bridge initialized");
            });
            """
            self.web_view.page().runJavaScript(script)
            print("[MainWindow] QWebChannel bridge setup complete")

        except ImportError:
            print("[MainWindow] QWebChannel not available, using fallback")
            # Fallback: use page script injection
            self.bridge = QtBridge(self)

    def showEvent(self, event):
        """Print window info when shown."""
        super().showEvent(event)
        print(f"[Window] Shown: size={self.size()}, pos={self.pos()}")
        print(f"[Window] isMaximized={self.isMaximized()}, isMinimized={self.isMinimized()}")
        print(f"[Window] winId={int(self.winId())}")

    def changeEvent(self, event):
        """Track window state changes."""
        if event.type() == event.Type.WindowStateChange:
            state = self.windowState()
            print(f"[Window] State changed: {state}")
            print(f"[Window] isMaximized={self.isMaximized()}, isMinimized={self.isMinimized()}")
        super().changeEvent(event)

    def closeEvent(self, event):
        """Handle close with confirmation."""
        print("[Window] closeEvent triggered")
        # Let the title bar handle confirmation, or do it here
        event.accept()

    # Native window operations - these should just work
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
# 7. Main Entry Point
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("ComfyUI-EZi - PySide6 Proof of Concept")
    print("=" * 60)

    # Start proxy
    proxy_port = find_free_port()
    proxy_thread = threading.Thread(target=start_proxy, args=(proxy_port,), daemon=True)
    proxy_thread.start()
    time.sleep(1)  # Let proxy start

    # Create Qt app
    app = QApplication(sys.argv)
    app.setApplicationName("ComfyUI-EZi-Qt")
    app.setApplicationDisplayName("ComfyUI-EZi Desktop")

    # Create main window
    window = MainWindow(proxy_port)
    window.show()

    print(f"\n[Main] Window shown. Test these:")
    print(f"  1. Click minimize (-) button -> should minimize to taskbar")
    print(f"  2. Click maximize (□) button -> should fill screen (not fullscreen)")
    print(f"  3. Click close (✕) button -> should show confirmation")
    print(f"  4. Drag title bar -> should move window")
    print(f"  5. Check taskbar preview -> should show window content")
    print(f"  6. Try Win+arrow keys -> should snap to zones")
    print(f"  7. Try Shift+drag -> should trigger FancyZones")
    print(f"\n[Main] Close window or press Ctrl+C to exit\n")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
