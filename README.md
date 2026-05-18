# ComfyUI-EZi PySide6 Porting Roadmap


## Goal

The aim is to replace pywebview with a PySide6-based desktop shell, keep the current launcher logic and everything else that is possible, just making slight changes and try to make it bit more flexible than earlier.
Also my goal is to learn more about programming and get more familiar with how PySide6 works.

## Project scope

This migration focuses on:
- Replacing pywebview window creation with a PySide6 main window.
- Replacing the JS bridge with a Qt-compatible bridge layer.
- Keeping the existing proxy-based shell loading model.
- Preserving current launcher features before adding new polish.

## **IMPORTANT**
- This migration does **not** aim to rewrite ComfyUI itself or replace the existing [Comfyui-Easy-Install](https://github.com/Tavris1/ComfyUI-Easy-Install). The goal is to experiment for my own learning and fun, high possibility to **not** work at any point.
- ❤️Big thanks to Tavris1 for the original Easy install. If you use ComfyUi, I **REALLY** recommend to check out and give star to the original [Comfyui-Easy-Install](https://github.com/Tavris1/ComfyUI-Easy-Install) by Tavris1 ❤️

## Roadmap

### Phase 0 — Setup

- [ ] Add PySide6 as the main GUI dependency.
- [ ] Confirm required supporting packages are installed.
- [ ] Remove pywebview and WebView2-specific startup checks.
- [ ] Remove pywebview cache-clearing and other dead WebView2-only code paths.
- [ ] Set up a clean branch or separate porting workspace for the migration.

### Phase 1 — Main window

- [ ] Create a `MainWindow` class based on `QMainWindow`.
- [ ] Replace `webview.create_window(...)` with native Qt window creation.
- [ ] Add a central web area for the launcher shell content.
- [ ] Port window lifecycle handling such as load, show, close, and close confirmation.
- [ ] Replace pywebview window-handle helpers with Qt-native window access.

### Phase 2 — JS/Python bridge

- [ ] Replace `pywebview.api` usage with a Qt bridge layer via `QWebChannel`.
- [ ] Add a bridge object that exposes launcher actions to the frontend.
- [ ] Register all required methods used by the current shell UI.
- [ ] Support promise-style return values for methods currently awaited in JavaScript.
- [ ] Verify that existing launcher actions still round-trip correctly between frontend and Python.

### Phase 3 — Frontend API migration

- [ ] Update the shell HTML/JS to stop calling `pywebview.api.*`.
- [ ] Replace those calls with the new Qt bridge API.
- [ ] Audit all existing frontend actions, including settings, folders, version switching, clipboard, cache, downloads, and modal actions.
- [ ] Confirm that any return-value methods still behave correctly in the UI.

### Phase 4 — File dialogs and native UI helpers

- [ ] Replace pywebview file/folder dialogs with Qt file dialogs.
- [ ] Port folder picker behavior.
- [ ] Port executable picker behavior.
- [ ] Port image picker behavior.
- [ ] Port save dialogs used for screenshots, recordings, and blob downloads.

### Phase 5 — Native window behavior

- [ ] Recreate frameless window behavior in Qt only if it is still worth keeping.
- [ ] Port resize-edge and resize-corner behavior using Qt/Win32 integration.
- [ ] Port snap support and test normal Windows snapping behavior.
- [ ] Port drag behavior from the custom HTML grip area if using a custom title bar.
- [ ] Re-test maximize, minimize, restore, close confirmation, and taskbar behavior.

### Phase 6 — Title, icon, and UI updates

- [ ] Replace title updates with Qt-native title handling.
- [ ] Replace icon setup with Qt-native icon loading.
- [ ] Replace Python-to-JS UI update calls with Qt JavaScript execution methods.
- [ ] Confirm launcher notifications and console output still reach the UI correctly.

### Phase 7 — Proxy and backend reuse

- [ ] Keep the existing proxy and HTTP shell-serving flow where possible.
- [ ] Verify that the shell still loads from the local proxy endpoint.
- [ ] Reuse existing launcher backend logic rather than rewriting working core behavior unnecessarily.

### Phase 8 — App entry point

- [ ] Replace the pywebview startup path with a `QApplication`-based entry point.
- [ ] Instantiate the Qt main window and connect it to the existing launcher API/backend.
- [ ] Restore saved window state at launch.
- [ ] Confirm clean shutdown and restart behavior.

### Phase 9 — Feature testing

#### Basic shell
- [ ] Window opens correctly.
- [ ] Main shell UI loads correctly.
- [ ] Window controls work correctly.
- [ ] Dragging and resizing work correctly.
- [ ] Snapping works correctly.

#### ComfyUI integration
- [ ] Proxy serves the shell correctly.
- [ ] ComfyUI loads correctly in the embedded view.
- [ ] Console output reaches the launcher UI.
- [ ] UI/console toggles still work.
- [ ] Reload behavior still works.

#### Bridge and tools
- [ ] All bridge methods are reachable from the frontend.
- [ ] Promise-style bridge methods work correctly.
- [ ] File dialogs work correctly.
- [ ] Screenshot saving works correctly.
- [ ] Recording flow still works.

#### Window state and polish
- [ ] Position and size restore correctly.
- [ ] Maximized state restores correctly.
- [ ] DPI scaling behaves correctly.
- [ ] Taskbar icon appears correctly.
- [ ] Close confirmation works correctly.

#### Edge cases
- [ ] Port-in-use errors are handled cleanly.
- [ ] Restart-after-update flow still works.
- [ ] Detached console mode still works if kept.
- [ ] Auth and external-link handling are re-tested after migration.

### Phase 10 — Cleanup

- [ ] Remove old pywebview helper functions and dead compatibility code.
- [ ] Remove WebView2-specific checks and messages.
- [ ] Update user-facing error messages to refer to PySide6 where relevant.
- [ ] Remove temporary migration shims once the new bridge is stable.
- [ ] Review the codebase for pywebview leftovers and stale comments.

## Suggested milestone order

### Milestone 1 — Working shell
- [ ] Qt app starts.
- [ ] Main window opens.
- [ ] Shell content loads.
- [ ] ComfyUI can be displayed.

### Milestone 2 — Working bridge
- [ ] Frontend can call Python actions.
- [ ] Settings can be loaded and saved.
- [ ] Core launcher buttons work.

### Milestone 3 — Feature parity
- [ ] Console panel works.
- [ ] Folder and file actions work.
- [ ] Version and path management work.
- [ ] Window state saving works.

### Milestone 4 — Native polish
- [ ] Snap and resize behavior feel reliable.
- [ ] Close/minimize/maximize behavior is solid.
- [ ] Dialogs, icons, and titles are fully native.

### Milestone 5 — Post-port improvements
- [ ] Revisit notes feature.
- [ ] Improve status display and diagnostics.
- [ ] Revisit custom title bar only if native behavior remains solid.
- [ ] Add future launcher-only features on top of the new foundation.

## Definition of done

The port can be considered complete when:
- [ ] Pywebview is fully removed.
- [ ] The launcher opens and controls ComfyUI successfully.
- [ ] The frontend can communicate with Python through the new Qt bridge.
- [ ] File dialogs, settings, window state, and console features still work.
- [ ] Window behavior is at least as reliable as the old launcher, and ideally better.
- [ ] The new codebase is clean enough to continue future development without carrying pywebview hacks forward.

## Notes

This roadmap is intentionally focused on migration tasks and feature parity first. New feature work should happen after the launcher is stable on PySide6, unless a feature directly helps test the new architecture.
