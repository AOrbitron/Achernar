import os
import threading
import time


import yaml
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import platform

# 加载账户信息

with open('config.yaml', 'r', encoding='utf-8') as f:
    data = yaml.load(f.read(), Loader=yaml.FullLoader)


app = Flask(__name__)

# 全局变量，存储最新的隧道地址
tunnel_url = None

chrome_options = Options()

# 根据操作系统判断是否需要添加特定参数
if platform.system() == 'Linux':
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')  # 修复 DevToolsActivePort 错误
    chrome_options.add_argument('--disable-dev-shm-usage')  # 修复共享内存问题

chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--ignore-ssl-errors")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")


def start_instance(email, password):
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1800, 1000)

        driver.get("https://www.kaggle.com/account/login")
        print(f"尝试登录账户 {email}")

        try:
            # 点击登录按钮并输入邮箱与密码
            login_button_xpath = '//*[@id="site-content"]/div[2]/div/div/div[1]/form/div/div/div[1]/button[2]'
            email_input_xpath = '//*[@id=":r0:"]'
            password_input_xpath = '//*[@id=":r1:"]'
            submit_button_xpath = '//*[@id="site-content"]/div[2]/div[1]/div/div[1]/form/div/div[4]/button[2]'

            # 等待登录按钮可点击并点击
            WebDriverWait(driver, 1000).until(
                EC.element_to_be_clickable((By.XPATH, login_button_xpath))
            ).click()
            time.sleep(1)

            # 输入邮箱
            WebDriverWait(driver, 1000).until(
                EC.presence_of_element_located((By.XPATH, email_input_xpath))
            ).send_keys(email)

            # 输入密码
            driver.find_element(By.XPATH, password_input_xpath).send_keys(password)

            # 点击提交按钮
            driver.find_element(By.XPATH, submit_button_xpath).click()
            print("登录信息已提交。")
        except Exception as login_error:
            print("\033[91m登录失败：" + str(login_error) + "\033[0m")
            return

        # 访问目标页面
        time.sleep(5)  # 等待登录完成

        driver.get(data["shared_notebook"])
        print("尝试运行项目")

        # 等待目标页面完全加载（等待特定的 <span> 元素出现）
        try:
            edit_button_xpath='//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/div[2]/span/a/button'
            WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, edit_button_xpath))).click()
        except:
            try:
                edit_button = '//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/a/button'
                WebDriverWait(driver, 60).until(
                    EC.element_to_be_clickable((By.XPATH, edit_button))
                ).click()
            except:
                print("不知道喵")
            return

        # 尝试运行项目
        try:
            time.sleep(10)  # 等待项目加载完成
            save_version = '//*[@id="site-content"]/div[2]/div[3]/div/div[1]/div/div/div[4]/div[1]/button'  # copy and edit按钮
            WebDriverWait(driver, 1000).until(
                EC.element_to_be_clickable((By.XPATH, save_version))
            ).click()
            time.sleep(10)
            confirm_button_xpath = '//*[@id="kaggle-portal-root-global"]/div/div[3]/div/div/div[4]/div[2]/button[2]'
            WebDriverWait(driver, 1000).until(
                EC.element_to_be_clickable((By.XPATH, confirm_button_xpath))
            ).click()

            print("项目运行中...")
            time.sleep(10)  # 等待运行完成
            driver.get("https://www.kaggle.com/")  # 返回主页准备润
            account_button_xpath = '//*[@id="site-container"]/div/div[4]/div[2]/div[2]/div/div/div/div'
            confirm_button_xpath = '//*[@id="kaggle-portal-root-global"]/div/div[3]/div/div/ul[2]/div/li'

            WebDriverWait(driver, 1000).until(
                EC.element_to_be_clickable((By.XPATH, account_button_xpath))
            ).click()
            time.sleep(1.5)

            WebDriverWait(driver, 1000).until(
                EC.element_to_be_clickable((By.XPATH, confirm_button_xpath))
            ).click()
            # 退出登录
        except Exception as run_error:
            print("\033[91m运行失败：" + str(run_error) + "\033[0m")

    except Exception as e:
        print("\033[91m任务失败：" + str(e) + "\033[0m")

    finally:
        if driver:
            print(f"任务完成，浏览器将关闭")
            cpolar_main() #刷新一下隧道
            time.sleep(5)  # 减少等待时间，可根据需要调整
            driver.quit()


def main():
    try:
        index=0
        accounts = data['kaggle_accounts']

        email, password = accounts[index]['email'], accounts[index]['password']

        while True:
            print(f"========== 开始第 {index} 次运行，使用账户：{email} ==========")
            start_instance(email, password)
            # logout_kaggle(run, email, password)
            # 可选：在两次运行之间添加延时，避免过快执行
            time.sleep(data['kaggle_change_account_interval'])
            index += 1
            if index >= len(accounts):
                index = 0

    except Exception as e:
        print("\033[91m任务中断：" + str(e) + "\033[0m")


def cpolar_main():
    global tunnel_url
    login_url = "https://dashboard.cpolar.com/login"
    info_url = "https://dashboard.cpolar.com/status"
    credentials = {
        'login': data["cpolar"]["email"],
        'password': data["cpolar"]["password"]
    }

    def fetch_info_from_website(login_url, info_url, credentials):
        with requests.Session() as session:
            login_page = session.get(login_url)
            login_page_soup = BeautifulSoup(login_page.text, 'html.parser')

            csrf_token = login_page_soup.find('input', {'name': 'csrf_token'})['value']
            credentials['csrf_token'] = csrf_token

            login_response = session.post(login_url, data=credentials)

            if login_response.url == login_url:
                print("登录失败，请检查您的凭据。")
                return None
            else:
                print("登录成功。")

            response = session.get(info_url)
            response.raise_for_status()

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                table_rows = soup.select("table tbody tr")
                for row in table_rows:
                    columns = row.find_all("td")
                    if len(columns) > 0:
                        url_column = row.find("a")
                        tunnel_url = url_column['href'] if url_column else "N/A"
                        return tunnel_url.replace("http://", "https://")
            else:
                print("未找到隧道信息表格。")
                return None

    new_tunnel_url = fetch_info_from_website(login_url, info_url, credentials)
    if new_tunnel_url:
        tunnel_url = new_tunnel_url
        print(f"最新隧道信息: {tunnel_url}")
    else:
        print("获取隧道信息失败。")
def schedule_cpolar_main(): #cpolar定时任务
    while True:
        cpolar_main()
        time.sleep(data['cpolar_check_interval'])


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def proxy_request(path):
    global tunnel_url
    if not tunnel_url:
        return jsonify({"error": "隧道地址未初始化，请稍后再试"}), 503

    print(f"收到外部请求：{request.method} {request.url}")

    try:
        # 获取请求数据
        if request.method == 'GET':
            external_request = request.args.to_dict()
        else:
            external_request = request.get_json()

        # 构建新的URL
        modified_tunnel_url = f"{tunnel_url}/{path}"
        if request.query_string:
            modified_tunnel_url += f"?{request.query_string.decode('utf-8')}"

        print(f"转发至新的隧道地址：{modified_tunnel_url}")
        if data['proxy'] is not None and data['proxy'] != '':
            proxy = data['proxy']
            os.environ["http_proxy"]=proxy
            os.environ["https_proxy"]=proxy
        else:
            proxies = None
        # 转发请求
        # 不要设置 Content-Type, 让 requests 自动处理
        headers = {key: value for key, value in request.headers.items() if key.lower() != 'host'}

        response = requests.request(request.method, modified_tunnel_url, params=request.args if request.method == 'GET' else None,
                                    json=external_request if request.method in ['POST', 'PUT', 'PATCH'] else None,
                                    data=request.get_data() if request.method not in ['GET', 'POST', 'PUT', 'PATCH'] else None,
                                    headers=headers, stream=True)

        print(f"转发请求完成，响应状态码：{response.status_code}")
        # 打印原始响应头
        print(f"原始响应头：{response.headers}")

        # 直接传递原始响应内容和头部给客户端
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk

        # 移除可能会导致问题的头部
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in response.headers.items()
                   if name.lower() not in excluded_headers]

        return Response(generate(), response.status_code, headers)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    if data["enable_cpolar_extension"]:
        threading.Thread(target=schedule_cpolar_main, daemon=True).start()
    if data["enable_kaggle_extension"]:
        threading.Thread(target=main, daemon=True).start()

    app.run(host='0.0.0.0', port=data['port'])
