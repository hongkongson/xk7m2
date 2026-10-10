"""在局域网里发布「哈哈哈」页面 —— **不需要外网**。

原理：本机开一个网页服务，同一个网（同一个 WiFi / 同一个交换机）里的
任何人，用浏览器打开 http://<本机内网IP>:8899/ 就能看到。

不经过任何外部服务器，所以：
  * 断网也能开（只要路由器还在工作）
  * 公司内网能开
  * 不会把任何东西发到公网上

关掉：直接关这个黑窗口，或者按 Ctrl+C。
"""

from __future__ import annotations

import http.server
import socket
import sys
from pathlib import Path

PORT = 8899
ROOT = Path(__file__).resolve().parent


class Handler(http.server.SimpleHTTPRequestHandler):
    """比默认的多做两件小事。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def guess_type(self, path):
        # 默认只给 text/html，不带 charset —— 明确带上 UTF-8，
        # 中文才不会因为浏览器猜错编码变成乱码。
        if str(path).endswith((".html", ".htm")):
            return "text/html; charset=utf-8"
        return super().guess_type(path)

    def end_headers(self):
        # 改完页面立刻生效，省得浏览器一直拿旧的缓存
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        print("  访问：%s" % (fmt % args), flush=True)


def lan_ips() -> list[str]:
    """列出本机所有内网 IPv4，告诉用户该把哪个地址发给别人。"""
    ips: list[str] = []
    try:
        # 不去真的连外网，只是让系统选出「对外的那张网卡」
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("10.255.255.255", 1))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:  # noqa: BLE001 - 断网时会走到这里，正常
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None,
                                       socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:  # noqa: BLE001
        pass
    return ips


def main() -> int:
    if not (ROOT / "index.html").exists():
        print(f"找不到 {ROOT / 'index.html'}")
        return 1

    try:
        httpd = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    except OSError as exc:
        print(f"端口 {PORT} 起不来：{exc}")
        print("可能有别的程序占着，改 serve.py 里的 PORT 再试。")
        return 1

    print("=" * 58)
    print("  哈哈哈页面已发布（局域网内可访问，不需要外网）")
    print("=" * 58)
    print()
    print("  本机自己测试：")
    print(f"      http://127.0.0.1:{PORT}/")
    print()
    print("  发给同一个网里的别人（手机连同一个 WiFi 也行）：")
    for ip in lan_ips():
        print(f"      http://{ip}:{PORT}/")
    print(f"      http://{socket.gethostname()}:{PORT}/   （有些网络认主机名）")
    print()
    print("  目录：", ROOT)
    print("  关掉：关这个窗口，或者按 Ctrl+C")
    print()
    print("-" * 58)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
