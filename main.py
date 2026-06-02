import os
import random
import threading
import time
import traceback
import json
import shutil
import subprocess
import stat
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, Response
import requests
import platform

# 加载账户信息
with open('config.yaml', 'r', encoding='utf-8') as f:
    data = yaml.load(f.read(), Loader=yaml.FullLoader)

app = Flask(__name__)

# 全局变量，存储最新的隧道地址
tunnel_url = []
global url_index
url_index = 0


# =====================================================================
#                       Kaggle CLI 核心代码开始
# =====================================================================

def write_kaggle_credentials(username, key, account_proxy=None):
    """
    物理写入 Kaggle 认证文件，并返回对应的环境变量字典。
    """
    env = os.environ.copy()

    # 强制 Kaggle 官方工具子进程：全局使用 UTF-8 编码处理所有读写和输出，防止中文 Windows 乱码崩溃
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'

    kaggle_dir = Path(os.path.expanduser('~')) / '.kaggle'
    kaggle_dir.mkdir(parents=True, exist_ok=True)

    # 判断是否为最新版 Token (KGAT_ 开头)
    if key.startswith("KGAT_"):
        token_file = kaggle_dir / 'access_token'
        with open(token_file, 'w', encoding='utf-8') as f:
            f.write(key)
        os.chmod(token_file, stat.S_IRUSR | stat.S_IWUSR)

        env['KAGGLE_API_TOKEN'] = key
        env.pop('KAGGLE_USERNAME', None)
        env.pop('KAGGLE_KEY', None)
    else:
        token_file = kaggle_dir / 'kaggle.json'
        with open(token_file, 'w', encoding='utf-8') as f:
            json.dump({"username": username, "key": key}, f)
        os.chmod(token_file, stat.S_IRUSR | stat.S_IWUSR)

        env['KAGGLE_USERNAME'] = username
        env['KAGGLE_KEY'] = key
        env.pop('KAGGLE_API_TOKEN', None)

    # 【账号级网络隔离核心】
    # 优先使用账号专属代理 account_proxy；没有则降级使用全局代理 quest_proxy/proxy
    proxy = account_proxy or data.get('quest_proxy') or data.get('proxy')
    if proxy:
        env['HTTP_PROXY'] = proxy
        env['HTTPS_PROXY'] = proxy
        print(f"[{username}] 网络通道已挂载代理: {proxy}")
    else:
        print(f"[{username}] ⚠️ 警告：当前账号未使用代理，将暴露本地真实 IP！")

    return env


def run_notebook_via_cli(username, key, notebook_file, account_proxy=None):
    """
    通过 subprocess 调用官方 CLI 工具进行推送
    """
    temp_folder = f"./temp_push_{username}"
    try:
        # 1. 物理写入凭据 & 准备独立的 CLI 环境变量（包含专属代理）
        custom_env = write_kaggle_credentials(username, key, account_proxy)

        # 2. 准备推送用的临时文件夹
        os.makedirs(temp_folder, exist_ok=True)
        shutil.copy(notebook_file, os.path.join(temp_folder, notebook_file))

        # 格式化项目名 (全小写，替换下划线为横杠)
        kernel_slug = notebook_file.split('.')[0].lower().replace('_', '-')
        if len(kernel_slug) < 5:
            kernel_slug += "-task"

        # 生成 metadata
        meta = {
            "id": f"{username}/{kernel_slug}",
            "title": kernel_slug,
            "code_file": notebook_file,
            "language": "python",
            "kernel_type": "notebook",
            "is_private": "true",
            "enable_gpu": "true",
            "enable_internet": "true",
            "dataset_sources": [],
            "competition_sources": [],
            "kernel_sources": []
        }

        metadata_path = os.path.join(temp_folder, 'kernel-metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)

        # 3. 使用系统终端运行 Kaggle CLI 提交，并指定 T4 显卡
        print(f"[{username}] 正在调用 CLI 将 {notebook_file} 提交到云端运行...")
        cmd = f'kaggle kernels push -p "{temp_folder}" --accelerator NvidiaTeslaT4'

        # 使用 utf-8 替换模式，防止 gbk 报错
        result = subprocess.run(cmd, shell=True, env=custom_env, capture_output=True, text=True, encoding='utf-8',
                                errors='replace')

        if result.returncode == 0:
            print(f"[{username}] 🎉 提交成功！项目已在 Kaggle 后台运行。")
            success = True
        else:
            print(f"[{username}] ❌ 提交失败，CLI 退出码: {result.returncode}")
            print(f"错误详情: {result.stderr.strip()}")
            print(f"标准输出: {result.stdout.strip()}")
            success = False

    except Exception as e:
        print(f"[{username}] ❌ 发生异常: {str(e)}")
        success = False

    finally:
        # 无论成功失败，确保清理临时文件夹
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)

    return success


def main():
    try:
        accounts = data.get('kaggle_accounts', [])
        if not accounts:
            print("❌ 配置错误：在 config.yaml 中没有找到 kaggle_accounts")
            return

        print(f"========== 启动完成，共 {len(accounts)} 个账户 ==========")
        print("💡 纯 API (Subprocess) 模式启动，安全稳定，自动切换身份！")
        print("项目地址：https://github.com/avilliai/Achernar  点个star喵，点个star谢谢喵")

        notebook_file = data.get('shared_notebook', "dania-fix.ipynb")

        if not os.path.exists(notebook_file):
            print(f"⚠️ 错误：在当前目录下找不到 '{notebook_file}'，请确认它在项目根目录中！")
            return

        index = 0
        retry_count = 0  # 记录当前账号的连续失败次数
        max_retries = 3  # 设置最大重试次数
        retry_interval = 60  # 失败后的重试等待时间（秒）

        while True:
            account = accounts[index]
            username = account.get('username')
            key = account.get('key') or account.get('password')
            account_proxy = account.get('proxy') or data.get('quest_proxy')

            if not username or not key:
                print(f"⚠️ 账号配置缺失 (缺少 username 或 key): {account}")
                index = (index + 1) % len(accounts)
                continue

            if retry_count == 0:
                print(f"\n========== 开始第 {index + 1} 个账户运行，账号：{username} ==========")
            else:
                print(f"\n========== 账号：{username} (第 {retry_count}/{max_retries} 次重试) ==========")

            # 运行提交任务
            success = run_notebook_via_cli(username, key, notebook_file, account_proxy)

            if success:
                # 提交成功：重置重试次数，执行正常的长休眠，并切换到下一个账号
                retry_count = 0
                interval = data.get('kaggle_change_account_interval', 43050)
                print(f"[{username}] 提交成功，等待 {interval} 秒后切换下一个账号...")
                time.sleep(interval)

                index = (index + 1) % len(accounts)

            else:
                # 提交失败：增加重试次数
                retry_count += 1
                if retry_count <= max_retries:
                    # 还在重试次数内：短休眠，不增加 index（下次循环依然是当前账号）
                    print(f"[{username}] 提交遇到错误，{retry_interval} 秒后进行第 {retry_count} 次重试...")
                    time.sleep(retry_interval)
                else:
                    # 超过最大重试次数：放弃当前账号，切换下一个
                    print(f"[{username}] 连续 {max_retries} 次提交失败，放弃当前账号，切换下一个。")
                    retry_count = 0  # 重置重试状态给下一个账号用

                    # 可选：如果希望即便失败也要等很久才切号，把这里的 time.sleep 改成长休眠
                    time.sleep(5)

                    index = (index + 1) % len(accounts)

    except Exception as e:
        print(f"\033[91m任务中断：{str(e)}\033[0m")
        traceback.print_exc()


# =====================================================================
#                       原有的 Cpolar 和 API 转发代码
# =====================================================================

def cpolar_main():
    global tunnel_url
    login_url = "https://dashboard.cpolar.com/login"
    info_url = "https://dashboard.cpolar.com/status"
    credentials = {
        'login': data["cpolar"]["email"],
        'password': data["cpolar"]["password"]
    }
    for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
        if var in os.environ:
            del os.environ[var]

    session = requests.Session()

    def login(session, login_url, credentials):
        try:
            login_page = session.get(login_url)
            login_page_soup = BeautifulSoup(login_page.text, 'html.parser')

            csrf_token = login_page_soup.find('input', {'name': 'csrf_token'})['value']
            credentials['csrf_token'] = csrf_token

            login_response = session.post(login_url, data=credentials)

            if login_response.url == login_url:
                print("登录失败，请检查您的凭据。")
                return False
            else:
                print("登录成功。")
                return True
        except Exception as e:
            print(f"登录失败：{str(e)}")
            return False

    def fetch_info_from_website(session, info_url):
        try:
            response = session.get(info_url)
            response.raise_for_status()

            if response.status_code == 200:
                tunnels = []
                soup = BeautifulSoup(response.text, 'html.parser')
                table_rows = soup.select("table tbody tr")
                row = table_rows[-1] if table_rows else None
                if row:
                    columns = row.find_all("td")
                    if len(columns) > 0:
                        url_column = row.find("a")
                        newurl = url_column['href'] if url_column else "N/A"
                        tunnels.append(newurl.replace("http://", "https://"))

                try:
                    row = table_rows[-3] if table_rows else None
                    if row:
                        columns = row.find_all("td")
                        if len(columns) > 0:
                            url_column = row.find("a")
                            newurl = url_column['href'] if url_column else "N/A"
                            tunnels.append(newurl)
                except Exception as e:
                    print(f"获取隧道信息2失败：{str(e)}")
                return tunnels
            return None
        except Exception as e:
            print(f"获取隧道信息失败：{str(e)}")
            return None

    login(session, login_url, credentials)

    while True:
        new_tunnel_url = fetch_info_from_website(session, info_url)
        if new_tunnel_url != None and new_tunnel_url != []:
            tunnel_url = new_tunnel_url
            print(f"最新隧道信息: {tunnel_url}")
        else:
            print("获取隧道信息失败，重新登录中...")
            if not login(session, login_url, credentials):
                print("无法重新登录。")
                time.sleep(data['cpolar_check_interval'])
                continue
            new_tunnel_url = fetch_info_from_website(session, info_url)
            if new_tunnel_url != [] and new_tunnel_url != None:
                tunnel_url = new_tunnel_url
                print(f"最新隧道信息: {tunnel_url}")

        time.sleep(data['cpolar_check_interval'])


def schedule_cpolar_main():
    cpolar_main()


def get_dynamic_ip():
    global tunnel_url
    get_ip_url = data["get_dynamic_ip"]["url"]

    def fetch_info_from_website():
        try:
            response = requests.get(get_ip_url)
            ip_address = response.text
            tunnels = [f"https://{ip_address}:{data['get_dynamic_ip']['port1']}",
                       f"https://{ip_address}:{data['get_dynamic_ip']['port2']}"]
            return tunnels
        except Exception as e:
            print(f"获取隧道信息失败：{str(e)}")
            return None

    while True:
        new_tunnel_url = fetch_info_from_website()
        if new_tunnel_url != None and new_tunnel_url != []:
            tunnel_url = new_tunnel_url
            print(f"最新隧道信息: {tunnel_url}")
        else:
            print("获取隧道信息失败")
            new_tunnel_url = fetch_info_from_website()
            if new_tunnel_url != [] and new_tunnel_url != None:
                tunnel_url = new_tunnel_url
                print(f"最新隧道信息: {tunnel_url}")

        time.sleep(data['cpolar_check_interval'])


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def proxy_request(path):
    global tunnel_url, url_index
    if not tunnel_url:
        return jsonify({"error": "隧道地址未初始化，请稍后再试"}), 503

    print(f"收到外部请求：{request.method} {request.url}")

    try:
        if request.method == 'GET':
            external_request = request.args.to_dict()
        else:
            external_request = request.get_json()

        if len(tunnel_url) == 1:
            url_index = 0

        current_url = tunnel_url[url_index]
        url_index = (url_index + 1) % len(tunnel_url)

        modified_tunnel_url = f"{current_url}/{path}"
        if request.query_string:
            modified_tunnel_url += f"?{request.query_string.decode('utf-8')}"

        print(f"转发至新的隧道地址：{modified_tunnel_url}")

        # 兼容原本配置的全局代理请求
        if data.get('quest_proxy'):
            proxy = data['quest_proxy']
            proxies = {"http": proxy, "https": proxy}
        else:
            proxies = None

        headers = {key: value for key, value in request.headers.items() if key.lower() != 'host'}

        response = requests.request(request.method, modified_tunnel_url,
                                    params=request.args if request.method == 'GET' else None,
                                    json=external_request if request.method in ['POST', 'PUT', 'PATCH'] else None,
                                    data=request.get_data() if request.method not in ['GET', 'POST', 'PUT',
                                                                                      'PATCH'] else None,
                                    headers=headers, stream=True, proxies=proxies)

        print(f"转发请求完成，响应状态码：{response.status_code}")

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in response.headers.items()
                   if name.lower() not in excluded_headers]

        return Response(generate(), response.status_code, headers)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    if data.get("enable_cpolar_extension"):
        threading.Thread(target=schedule_cpolar_main, daemon=True).start()

    if data.get("enable_kaggle_extension"):
        threading.Thread(target=main, daemon=True).start()

    if data.get("enable_get_dynamic_ip"):
        threading.Thread(target=get_dynamic_ip, daemon=True).start()

    app.run(host='0.0.0.0', port=data.get('port', 3529))