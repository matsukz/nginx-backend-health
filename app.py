from flask import Flask, render_template, request
import ipaddress
import subprocess
from pathlib import Path
import shutil
import requests

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

IP_LIST_FILE = BASE_DIR / "ip_list.txt"
NGINX_UPSTREAM_FILE = BASE_DIR / "upstream_servers.conf"
NGINX_UPSTREAM_BACKUP = BASE_DIR / "upstream_servers.conf.bak"

# nginxコマンド（環境に応じて調整）
NGINX_TEST_CMD = ["sudo", "nginx", "-t"]
NGINX_RELOAD_CMD = ["sudo", "nginx", "-s", "reload"]


def load_ip_list() -> str:
    if IP_LIST_FILE.exists():
        return IP_LIST_FILE.read_text(encoding="utf-8")
    return ""


def validate_ip(ip_str: str) -> bool:
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def http_test(ip_list, timeout=2, port=1234, path="/v1"):
    success_ips = []
    for ip in ip_list:
        ip = ip.strip()
        if not ip:
            continue
        if not validate_ip(ip):
            continue

        url = f"http://{ip}:{port}{path}"
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code < 400:
                success_ips.append(ip)
        except requests.RequestException:
            continue

    return success_ips


def write_nginx_upstream(ips, port=1234):
    text = "\n".join(f"server {ip}:{port};" for ip in ips) + "\n"
    NGINX_UPSTREAM_FILE.write_text(text, encoding="utf-8")


def nginx_test_config():
    """nginx -t を実行し、成功なら True、失敗なら False を返す"""
    try:
        result = subprocess.run(
            NGINX_TEST_CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return True, result.stderr + result.stdout
        else:
            return False, result.stderr + result.stdout
    except Exception as e:
        return False, str(e)


def reload_nginx():
    subprocess.run(NGINX_RELOAD_CMD, check=True)

def get_nginx_systemd_status():
    try:
        r = subprocess.run(
            ["systemctl", "is-active", "nginx"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        is_active = (r.stdout.strip() == "active")
        # 詳細が欲しければ is-active ではなく status --no-pager 等に変える
        return is_active, r.stdout + r.stderr
    except Exception as e:
        return False, str(e)


@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    error = ""

    ip_list_text = load_ip_list()
    success_ip_list_text = ""

    nginx_is_active, nginx_status_message = get_nginx_systemd_status()

    if request.method == "POST":
        action = request.form.get("action")
        ip_list_text = request.form.get("ip_list", "")
        success_ip_list_text = request.form.get("success_ip_list", "")

        if action == "test":
            raw_ips = [line.strip() for line in ip_list_text.splitlines()]
            success_ips = http_test(raw_ips)

            if success_ips:
                success_ip_list_text = "\n".join(success_ips)
                message = f"テスト完了：{len(success_ips)} 件のIPにHTTPアクセス成功しました。"
            else:
                success_ip_list_text = ""
                error = "HTTPアクセスに成功したIPがありません。"

        elif action == "replace":
            raw_success_ips = [
                line.strip()
                for line in success_ip_list_text.splitlines()
                if line.strip()
            ]

            if not raw_success_ips:
                error = "置換対象のIPがありません。テスト結果を確認してください。"
            else:
                try:
                    # (1) まずバックアップを作成
                    if NGINX_UPSTREAM_FILE.exists():
                        shutil.copy2(NGINX_UPSTREAM_FILE, NGINX_UPSTREAM_BACKUP)

                    # (2) 新しい設定を書き込み
                    write_nginx_upstream(raw_success_ips, port=1234)

                    # (3) nginx -t を実行
                    ok, test_output = nginx_test_config()

                    if not ok:
                        # (4) エラー → ロールバック
                        if NGINX_UPSTREAM_BACKUP.exists():
                            shutil.copy2(NGINX_UPSTREAM_BACKUP, NGINX_UPSTREAM_FILE)
                        error = (
                            "nginx の構文チェックに失敗したため置換を中止しました。\n\n"
                            + test_output
                        )
                    else:
                        # (5) 構文チェック成功 → reload
                        reload_nginx()
                        message = (
                            f"置換 → nginx構文チェック → 再読み込み 完了（{len(raw_success_ips)} 件）"
                        )

                except Exception as e:
                    error = f"処理中にエラーが発生しました: {e}"

    return render_template(
        "index.html",
        ip_list_text=ip_list_text,
        success_ip_list_text=success_ip_list_text,
        message=message,
        error=error,
        nginx_upstream_file=str(NGINX_UPSTREAM_FILE),
        nginx_is_active=nginx_is_active,
        nginx_status_message=nginx_status_message,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)