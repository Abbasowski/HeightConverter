"""Height & Weight Converter — native Windows app (pywebview)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

APP_NAME = "HeightConverter"
APP_VERSION = "1.1.0"

# Where to look for newer releases (Latest release on this GitHub repo).
UPDATE_MANIFEST_URL = "https://api.github.com/repos/Abbasowski/HeightConverter/releases/latest"


class Api:
    """Exposed to JavaScript as window.pywebview.api.*"""

    def get_version(self):
        return APP_VERSION

    def check_update(self):
        """Ask GitHub for the latest release. Returns dict for the UI."""
        result = {
            "current": APP_VERSION,
            "latest": None,
            "downloadUrl": None,
            "notes": None,
            "updateAvailable": False,
            "error": None,
        }
        try:
            req = urllib.request.Request(
                UPDATE_MANIFEST_URL,
                headers={"User-Agent": APP_NAME + "/" + APP_VERSION, "Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
            latest = (data.get("tag_name") or "").lstrip("vV")
            url = None
            for asset in data.get("assets", []):
                name = (asset.get("name") or "").lower()
                if name.endswith(".zip") and APP_NAME.lower() in name:
                    url = asset.get("browser_download_url")
                    break
            if not url:
                for asset in data.get("assets", []):
                    if (asset.get("name") or "").lower().endswith(".zip"):
                        url = asset.get("browser_download_url")
                        break
            result["latest"] = latest or None
            result["downloadUrl"] = url
            result["notes"] = data.get("body")
            result["updateAvailable"] = bool(
                url and latest and _newer(latest, APP_VERSION)
            )
        except Exception as e:
            result["error"] = str(e)
        return result

    def download_and_install(self):
        """Download the update zip and swap the exe. Returns a status dict."""
        info = self.check_update()
        if not info.get("updateAvailable"):
            return {"ok": False, "message": info.get("error") or "بروزرسانی جدیدی وجود ندارد"}
        url = info["downloadUrl"]
        exe_dir = _exe_dir()
        if not os.path.isdir(exe_dir) or not os.path.isfile(os.path.join(exe_dir, APP_NAME + ".exe")):
            return {"ok": False, "message": "پوشه برنامه پیدا نشد"}

        zip_path = os.path.join(tempfile.gettempdir(), APP_NAME + "-update.zip")
        stage_dir = exe_dir + ".Update"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": APP_NAME + "/" + APP_VERSION})
            with urllib.request.urlopen(req, timeout=60) as resp, open(zip_path, "wb") as f:
                shutil.copyfileobj(resp, f)
            if os.path.getsize(zip_path) < 1024:
                raise RuntimeError("فایل دانلودشده نامعتبر است")
            if os.path.isdir(stage_dir):
                shutil.rmtree(stage_dir, ignore_errors=True)
            with __import__("zipfile").ZipFile(zip_path) as z:
                z.extractall(stage_dir)

            # If the zip wraps everything in one folder, unwrap it
            entries = os.listdir(stage_dir)
            if len(entries) == 1 and os.path.isdir(os.path.join(stage_dir, entries[0])):
                inner = os.path.join(stage_dir, entries[0])
                outer = stage_dir + ".outer"
                os.rename(stage_dir, outer)
                os.rename(inner, stage_dir)
                shutil.rmtree(outer, ignore_errors=True)

            batch = os.path.join(tempfile.gettempdir(), APP_NAME + "-update.bat")
            with open(batch, "w", encoding="utf-8") as b:
                b.write("@echo off\r\n")
                b.write("timeout /t 2 /nobreak >nul\r\n")
                b.write(f'del /f /q "{exe_dir}\\{APP_NAME}.exe"\r\n')
                b.write(f'xcopy /e /i /y "{stage_dir}" "{exe_dir}"\r\n')
                b.write(f'rmdir /s /q "{stage_dir}"\r\n')
                b.write(f'del /f /q "{zip_path}"\r\n')
                b.write(f'start "" "{exe_dir}\\{APP_NAME}.exe"\r\n')
            subprocess.Popen(["cmd", "/c", batch], creationflags=subprocess.CREATE_NO_WINDOW)
            return {"ok": True, "message": "بروزرسانی دانلود شد — برنامه ری‌استارت می‌شود"}
        except Exception as e:
            return {"ok": False, "message": "خطا در بروزرسانی: " + str(e)}


def _exe_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _newer(candidate: str, current: str) -> bool:
    def parts(v):
        return [int(x) for x in v.split(".") if x.isdigit()]
    try:
        return parts(candidate) > parts(current)
    except Exception:
        return False


def resource_path(relative: str) -> str:
    """Resolve a bundled resource both in dev and inside a frozen PyInstaller exe."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def main():
    html_path = resource_path('height-converter.html')
    webview.create_window(
        'تبدیل قد و وزن',
        html_path,
        js_api=Api(),
        width=560,
        height=780,
        min_size=(360, 500),
    )
    webview.start()


if __name__ == '__main__':
    import webview
    main()
