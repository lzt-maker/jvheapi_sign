import requests
import os
import sys

# ==================== 用户凭据配置 ====================
# 从环境变量读取，供 GitHub Actions 使用 Secrets 注入
USERNAME = os.environ.get("API_USERNAME")
PASSWORD = os.environ.get("API_PASSWORD")

if not USERNAME or not PASSWORD:
    print("错误：未找到用户名或密码环境变量！请检查 GitHub Secrets 配置。")
    sys.exit(1)

# 创建 Session 对象，自动保存和传递 Cookie（包括 refresh cookie）
SESSION = requests.Session()
ACCESS_TOKEN = ""
# ====================================================

def login():
    """自动登录获取最新的 Token 和 Cookie"""
    global ACCESS_TOKEN

    url = "https://api.zfb.la/api/user/login?turnstile="

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-store",
        "content-type": "application/json",
        "origin": "https://api.zfb.la",
        "priority": "u=1, i",
        "referer": "https://api.zfb.la/sign-in",
        "sec-ch-ua": '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0",
    }

    # 根据你提供的负载设置请求体
    payload = {"username": USERNAME, "password": PASSWORD}

    print("正在尝试登录...")
    try:
        response = SESSION.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            res_json = response.json()

            # 解析返回的 Token
            data = res_json.get("data", {})
            token = None
            if isinstance(data, dict):
                token = (
                    data.get("token")
                    or data.get("access_token")
                    or data.get("authorization")
                )
            elif isinstance(data, str):
                token = data

            if not token:
                token = res_json.get("token") or res_json.get("access_token")

            if token:
                if not token.startswith("Bearer "):
                    token = f"Bearer {token}"
                ACCESS_TOKEN = token
                print("登录成功！已获取最新的 Authorization Token。")
                return True
            else:
                print("登录成功，但解析 Token 失败，返回内容:", res_json)
                return False
        else:
            print(
                f"登录失败，HTTP 状态码: {response.status_code}，响应内容: {response.text}"
            )
            return False

    except requests.exceptions.RequestException as e:
        print(f"登录网络请求发生异常: {e}")
        return False


def do_checkin():
    """执行签到操作"""
    global ACCESS_TOKEN

    # 首次运行先登录
    if not ACCESS_TOKEN:
        if not login():
            print("未能完成登录，取消签到。")
            return

    url = "https://api.zfb.la/api/user/checkin"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "authorization": ACCESS_TOKEN,
        "cache-control": "no-store",
        "content-length": "0",
        "origin": "https://api.zfb.la",
        "priority": "u=1, i",
        "referer": "https://api.zfb.la/profile",
        "sec-ch-ua": '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0",
    }

    try:
        response = SESSION.post(url, headers=headers, timeout=10)

        # 如果 Token 在签到时失效，重新自动登录一次并重试签到
        if response.status_code == 401:
            print("Token 已失效，正在重新登录并重试...")
            if login():
                headers["authorization"] = ACCESS_TOKEN
                response = SESSION.post(url, headers=headers, timeout=10)

        if response.status_code == 200:
            res_json = response.json()
            message = res_json.get("message", "未获取到 message 字段")
            checkin_date = (
                res_json.get("data", {}).get("checkin_date", "未获取到签到日期")
            )

            print("========================================")
            print(f"签到提示: {message}")
            print(f"签到日期: {checkin_date}")
            print("========================================")
        else:
            print(f"签到失败，HTTP 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"签到请求发生异常: {e}")

if __name__ == "__main__":
    do_checkin()