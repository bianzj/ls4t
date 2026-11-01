"""Accept an Earthdata token locally, verify a real ZIP, and start the download.

Validated tokens are saved in the current user's private Windows DPAPI cache,
so later downloads can resume. Plaintext tokens never enter files or logs.
"""
import argparse
import html
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import download_daytime as downloader


def page(content):
    return ("<!doctype html><html lang='zh-CN'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Earthdata 下载连接</title><style>"
            "body{font:16px/1.7 system-ui;max-width:660px;margin:64px auto;padding:0 24px;color:#18252e}"
            "input{box-sizing:border-box;width:100%;padding:12px;font:inherit;border:1px solid #899ba5;border-radius:6px}"
            "button{background:#075b91;color:white;padding:12px 20px;border:0;border-radius:6px;font:inherit;margin-top:18px}"
            "code{overflow-wrap:anywhere}a{color:#075b91}</style>" + content + "</html>").encode("utf-8")


class ConnectionServer(HTTPServer):
    def __init__(self, root):
        super().__init__(("127.0.0.1", 0), Handler)
        self.root = root
        self.nonce = secrets.token_urlsafe(32)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.url = self.origin + "/?nonce=" + self.nonce
        self.child_pid = None
        self.timeout = 1


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, content):
        data = page(content)
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        query = parse_qs(urlparse(self.path).query)
        nonce = query.get("nonce", [""])[0]
        return secrets.compare_digest(nonce, self.server.nonce)

    def do_GET(self):
        if not self.authorized():
            self.reply(403, "<p>请使用本次任务打开的连接页面。</p>")
            return
        if self.server.child_pid:
            status = json.loads((self.server.root / "status.json").read_text(encoding="utf-8"))
            self.reply(200, f"<h1>Earthdata 下载任务</h1><p>进程：{self.server.child_pid}</p>"
                       f"<p>状态：{html.escape(status['state'])}</p>"
                       f"<p>已校验完成：{status['downloaded_scenes']} 景</p><p>刷新页面可查看进度。</p>")
            return
        self.reply(200, "<h1>连接 Earthdata 下载</h1>"
            "<p>非洲热带雨林 · S3A SLSTR · 2017—2020 年 · 仅白天</p>"
            "<p>在已登录的 Earthdata 个人页面中选择 <b>Generate Token</b>，复制下载令牌后粘贴到下方。</p>"
            "<p><a target='_blank' rel='noopener noreferrer' href='https://urs.earthdata.nasa.gov/profile'>打开 Earthdata 个人页面</a></p>"
            f"<form method='post' action='/connect?nonce={self.server.nonce}'>"
            "<label for='token'>Earthdata 下载令牌</label>"
            "<input id='token' name='token' type='password' autocomplete='off' required autofocus>"
            "<button type='submit'>保存令牌并续传</button></form>"
            "<p>验证成功后，令牌会加密保存在本机，随后自动续传；后续重启可自动读取。</p>")

    def do_POST(self):
        if (not self.authorized() or self.headers.get("Origin") != self.server.origin
                or self.headers.get("Content-Type", "").split(";")[0] != "application/x-www-form-urlencoded"):
            self.reply(403, "<p>连接请求来源不匹配，请重新打开本机连接页面。</p>")
            return
        if self.server.child_pid:
            self.reply(200, "<p>下载任务已启动，请刷新连接页面查看进度。</p>")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16384:
                self.reply(400, "<p>令牌输入长度不正确。</p>")
                return
            values = parse_qs(self.rfile.read(length).decode("utf-8"), max_num_fields=2)
            token = values.get("token", [""])[0].strip()
            if token.startswith("Bearer "):
                token = token[7:].strip()
            if not token or "\n" in token or "\r" in token:
                self.reply(400, "<p>请输入完整的下载令牌。</p>")
                return
            with downloader.connect(self.server.root) as db:
                row = db.execute("""SELECT metadata FROM products
                    WHERE state IN ('queued','failed') AND acquired>='2017-01-01'
                    AND acquired<'2021-01-01' ORDER BY acquired LIMIT 1""").fetchone()
            if not row:
                self.reply(409, "<p>当前没有待下载的 2017—2020 年影像。</p>")
                return
            url = json.loads(row[0])["DownloadUrl"]
            if urlparse(url).scheme != "https" or urlparse(url).hostname not in downloader.NASA_HOSTS:
                raise ValueError("Unexpected archive host")
            with downloader.session() as session:
                with session.get(url, headers={"Authorization": "Bearer " + token, "Range": "bytes=0-31"},
                                 stream=True, timeout=(20, 45)) as response:
                    prefix = next(response.iter_content(32), b"")
                    valid = response.status_code in (200, 206) and prefix.startswith(b"PK")
            if not valid:
                self.reply(401, "<h1>令牌验证未通过</h1><p>请确认令牌仍有效，并已授权 LAADS 数据访问；返回上一页重新输入。</p>")
                return
            downloader.save_earthdata_token(token)
            env = os.environ.copy()
            env.update(EARTHDATA_TOKEN=token, PYTHONUTF8="1")
            with (self.server.root / "download.log").open("ab") as out, (self.server.root / "download.err.log").open("ab") as err:
                process = subprocess.Popen([sys.executable, "-u", str(Path(__file__).with_name("download_daytime.py")),
                    "--provider", "earthdata", "--download", "--start-year", "2017", "--end-year", "2020",
                    "--root", str(self.server.root)], env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.server.child_pid = process.pid
            (self.server.root / "process.pid").write_text(str(process.pid), encoding="ascii")
            self.reply(200, f"<h1>令牌已加密保存，续传任务已启动</h1><p>进程：{process.pid}</p>"
                       "<p>程序会验证每个 ZIP，并在剩余空间达到预留阈值时停止。</p>"
                       f"<p><a href='/?nonce={self.server.nonce}'>查看下载进度</a></p>")
        except Exception:
            # Never print request bodies, Authorization headers, or exception objects.
            self.reply(502, "<p>连接或启动未成功，请稍后重试。</p>")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(r"D:\data\sentinel3\africa_rainforest_day_2017_2020_earthdata"))
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    with ConnectionServer(args.root) as server:
        info = {"url": server.url, "pid": os.getpid(), "expires_utc_epoch": time.time() + 1800}
        downloader.write_json(args.root / "earthdata_connection.json", info)
        deadline = time.monotonic() + 1800
        while time.monotonic() < deadline:
            server.handle_request()


if __name__ == "__main__":
    main()
