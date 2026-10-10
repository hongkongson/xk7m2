"""全自动：建 GitHub 仓库 -> 推 index.html -> 开 Pages -> 给出网址。

用你本地已存的 Git 凭据（credential.helper = manager）调 GitHub API。
不打印任何令牌内容。
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

REPO = "xk7m2"          # 随机名 —— 网址就是「意义不明」的样子
SITE = Path(r"E:\00_workspace\dsh\haha-site")
API = "https://api.github.com"
PROXY = None            # 走系统能通的路；下面会自动判断


def get_token() -> tuple[str, str]:
    """从 git 凭据里取 (用户名, 令牌)。"""
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, timeout=30,
    )
    user = token = ""
    for line in p.stdout.splitlines():
        if line.startswith("username="):
            user = line.split("=", 1)[1].strip()
        elif line.startswith("password="):
            token = line.split("=", 1)[1].strip()
    return user, token


def api(path: str, token: str, method: str = "GET", **kw):
    h = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = path if path.startswith("http") else API + path
    return httpx.request(method, url, headers=h, timeout=30.0, **kw)


def main() -> int:
    user, token = get_token()
    if not token:
        print("取不到令牌")
        return 1
    print(f"账号：{user}")
    print(f"令牌：有（{len(token)} 字符，不打印内容）")
    print()

    # ---------- 1. 看这个令牌能干什么 ----------
    r = api("/user", token)
    print(f"[1] 验证令牌    HTTP {r.status_code}", end="")
    if r.status_code != 200:
        print(f"  ✗ {r.text[:200]}")
        return 1
    scopes = r.headers.get("x-oauth-scopes", "（细粒度令牌，无 scopes 头）")
    print(f"    scopes: {scopes}")

    # ---------- 2. 建仓库 ----------
    print(f"\n[2] 创建仓库 {user}/{REPO}")
    r = api("/user/repos", token, method="POST", json={
        "name": REPO,
        "description": "",
        "private": False,       # Pages 免费版需要公开仓库
        "auto_init": False,
        "has_issues": False,
        "has_wiki": False,
        "has_projects": False,
    })
    if r.status_code == 201:
        print("    ✓ 建好了")
    elif r.status_code == 422:
        print("    已存在，直接复用")
    else:
        print(f"    ✗ HTTP {r.status_code}  {r.text[:300]}")
        print("\n    （很可能是这个令牌没有『创建仓库』权限 ——")
        print("      那就得你在网页上手动建一个，我再推）")
        return 1

    # ---------- 3. 推文件 ----------
    print(f"\n[3] 推送 index.html")
    env = {
        "GIT_AUTHOR_NAME": user, "GIT_AUTHOR_EMAIL": f"{user}@users.noreply.github.com",
        "GIT_COMMITTER_NAME": user, "GIT_COMMITTER_EMAIL": f"{user}@users.noreply.github.com",
    }
    import os
    run_env = dict(os.environ)
    run_env.update(env)
    run_env["GIT_TERMINAL_PROMPT"] = "0"

    def git(*args, check=True):
        p = subprocess.run(["git", *args], cwd=SITE, capture_output=True,
                           text=True, timeout=180, env=run_env)
        if check and p.returncode != 0:
            print(f"    git {' '.join(args)} 失败：{p.stderr.strip()[:300]}")
        return p

    git("init", "-q", "-b", "main", check=False)
    git("add", "-A")
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        git("commit", "-q", "-m", "x")
    url = f"https://github.com/{user}/{REPO}.git"
    git("remote", "remove", "origin", check=False)
    git("remote", "add", "origin", url)
    p = git("push", "-u", "origin", "main", "--force")
    if p.returncode != 0:
        return 1
    print("    ✓ 推上去了")

    # ---------- 4. 开 Pages ----------
    print("\n[4] 开启 GitHub Pages")
    r = api(f"/repos/{user}/{REPO}/pages", token, method="POST",
            json={"source": {"branch": "main", "path": "/"}})
    if r.status_code in (201, 204):
        print("    ✓ 已开启")
    elif r.status_code == 409:
        print("    已经开过了")
    else:
        print(f"    ✗ HTTP {r.status_code}  {r.text[:250]}")
        print("    → 需要你手动开：Settings → Pages → main / (root) → Save")

    # ---------- 5. 等它生效并验证 ----------
    site = f"https://{user}.github.io/{REPO}/"
    print(f"\n[5] 等 Pages 构建，然后验证 {site}")
    ok = False
    for i in range(20):
        time.sleep(10)
        try:
            rr = httpx.get(site, timeout=20.0, follow_redirects=True)
            if rr.status_code == 200 and "哈哈" in rr.text:
                print(f"    ✓ 第 {(i + 1) * 10} 秒：页面已生效！")
                ok = True
                break
            print(f"    …{i * 10 + 10}s  HTTP {rr.status_code}")
        except Exception as exc:  # noqa: BLE001
            print(f"    …{i * 10 + 10}s  {type(exc).__name__}")

    print("\n" + "=" * 58)
    if ok:
        print("  好了，把这个网址发给好友：")
    else:
        print("  推送完成，但 Pages 还没构建好（首次通常 1~3 分钟）。")
        print("  过一会儿自己访问这个网址：")
    print()
    print(f"      {site}")
    print()
    print("=" * 58)
    return 0


if __name__ == "__main__":
    sys.exit(main())
