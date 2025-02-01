import os
import random
import threading
import time


import yaml
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, Response

import requests
import platform

from playwright.sync_api import sync_playwright

# 加载账户信息

with open('config.yaml', 'r', encoding='utf-8') as f:
    data = yaml.load(f.read(), Loader=yaml.FullLoader)


app = Flask(__name__)

# 全局变量，存储最新的隧道地址
tunnel_url=[]
global url_index
url_index = 0

def start_instance(email, password):
    try:
        # 使用 Playwright 启动浏览器
        with sync_playwright() as p:
            launch_args = {
                "headless": data["headless"],  # 替换为你的 data["headless"]
                "args": ["--no-sandbox", "--disable-dev-shm-usage"]
            }
            proxy = data['proxy']
            if proxy!=None and proxy!='' and proxy!="":  # 如果 proxy 不为空
                launch_args["proxy"] = {
                    "server": proxy
                }
                print(f"使用代理 {proxy}")

            browser = p.chromium.launch(**launch_args)
            context = browser.new_context()

            # 打开新的页面
            page = context.new_page()

            # 访问登录页面
            page.goto("https://www.kaggle.com/account/login",timeout=900000)
            print(f"尝试登录账户 {email}")

            # 等待并填写登录信息
            login_button_xpath = '//*[@id="site-content"]/div[2]/div/div/div[1]/form/div/div/div[1]/button[2]'
            page.click(login_button_xpath)
            page.fill('//*[@id=":r0:"]', email)  # 填写邮箱
            page.fill('//*[@id=":r1:"]', password)  # 填写密码
            page.click('//*[@id="site-content"]/div[2]/div/div/div[1]/form/div/div[4]/button[2]')  # 提交登录表单

            print("登录信息已提交。")
            time.sleep(10)  # 等待登录完成

            # 访问目标页面
            page.goto(data["shared_notebook"],timeout=900000)  # 替换成目标页面的URL
            print("尝试运行项目")

            # 尝试运行项目
            time.sleep(10)  # 等待项目加载完成
            edit_buttons = [
                '//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/a/button',
                '//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/div[2]/span/a/button',
                '//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/div[2]/div/span/a/button'
            ]

            clicked = False
            for edit_button in edit_buttons:
                try:
                    page.wait_for_selector(edit_button, state="visible",
                                           timeout=30000)  # 使用wait_for_selector替换is_visable
                    page.click(edit_button)
                    print("已进入编辑页")
                    clicked = True
                    break
                except Exception as e:
                    print(f"尝试点击 {edit_button} 失败: 尝试使用其他xpath路径定位")
            print("等待页面加载完成")
            time.sleep(25)
            page.evaluate("""
                () => {
                    const blocker1 = document.querySelector('.sc-ftmehX.clyupM');
                    const blocker2 = document.querySelector('.MuiBackdrop-root');
                    if (blocker1) blocker1.style.pointerEvents = 'none';
                    if (blocker2) blocker2.style.pointerEvents = 'none';
                }
            """)

            save_version_buttons = [
                '//*[@id="site-content"]/div[2]/div/div[1]/div/div/div[4]/div[1]/button',
                '//*[@id="site-content"]/div[2]/div[2]/div/div[1]/div/div/div[4]/div[1]/button',
                '//*[@id="site-content"]/div[3]/div/div[1]/div/div/div[4]/div[1]/button'
            ]

            for save_version_button in save_version_buttons:
                try:
                    page.wait_for_selector(save_version_button, state="visible",
                                           timeout=30000)  # 使用wait_for_selector替换is_visable
                    page.click(save_version_button)
                    print("已保存版本")
                    break
                except Exception as e:
                    print(f"尝试点击 {save_version_button} 失败: 尝试使用其他xpath路径定位")
            time.sleep(15)
            confirm_buttions=[
                '//*[@id="kaggle-portal-root-global"]/div/div[3]/div/div/div[4]/div[2]/button[2]',
                '/html/body/div[2]/div[3]/div/div/div[4]/div[2]/button[2]'
                '//*[@id="kaggle-portal-root-global"]/div[2]/div[3]/div/div/div[4]/div[2]/button[2]',
                "//button[contains(., 'Save')]",  # 方案 2：利用文本内容
                "button:has-text('Save')",  # 方案4 利用文本内容
                "/html/body/div[contains(@class,'MuiDrawer-root') and contains(@class,'MuiDrawer-modal')]/div[contains(@class,'MuiDrawer-paper')]/div/div/div[last()]/div[last()]/button[last()]",
            ]
            try_buttons=True
            try:
                page.get_by_role("button", name="Save").click(timeout=40000)
                print("已确认运行 (使用 get_by_role)")
                try_buttons=False
            except Exception as e:
                print(f"尝试使用 get_by_role 点击失败: {e}")
            if try_buttons:
                for confirm_button in confirm_buttions:
                    try:
                        page.wait_for_selector(confirm_button, state="visible",
                                               timeout=30000)  # 使用wait_for_selector替换is_visable
                        page.click(confirm_button)
                        print("已确认运行")
                        break
                    except Exception as e:
                        print(f"尝试点击 {confirm_button} 失败: 尝试使用其他xpath路径定位")
            print("run")
            time.sleep(5)
            print("项目运行中...")
            page.goto("https://www.kaggle.com/",timeout=900000)  # 返回主页准备退出登录

            # 退出登录
            time.sleep(5)
            abx='//*[@id="site-container"]/div/div[3]/div[2]/div[2]/div/div/div/div/svg'

            avatar='//*[@id="site-container"]/div/div[3]/div[2]/div[2]/div/div/div/div/div'
            account_button_xpath = '//*[@id="site-container"]/div/div[4]/div[2]/div[2]/div/div/div/div'
            if page.is_visible(abx):
                page.click(abx)
                print("点击账户页面")
            elif page.is_visible(account_button_xpath):
                page.click(account_button_xpath)
                print("点击账户页面")
            elif page.is_visible(avatar):
                page.click(avatar)
                print("点击账户页面")
            else:
                print("未找到账户页面。不影响使用")
                return
            time.sleep(1.5)
            confirm_button_xpath = '//*[@id="kaggle-portal-root-global"]/div/div[3]/div/div/ul[2]/div/li'
            confirm_button_xpath2= '//*[@id="kaggle-portal-root-global"]/div/div[3]/div/div/ul[2]/div/li/div/a/div'
            if page.is_visible(confirm_button_xpath2):
                page.click(confirm_button_xpath2)
            else:
                page.click(confirm_button_xpath)

            time.sleep(1.5)



    except Exception as e:
        print(f"\033[91m任务失败：{str(e)}\033[0m")
          # 等待10秒后重试
    finally:
        if browser:
            print("任务完成，浏览器将关闭")
            try:
                browser.close()
            except Exception as e:
                print(f"{str(e)}")

def kill_instance(email, password):
    try:
        # 使用 Playwright 启动浏览器
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=data["headless"], args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context()

            # 打开新的页面
            page = context.new_page()


            # 访问登录页面
            page.goto("https://www.kaggle.com/account/login")
            print(f"尝试登录账户 {email}")

            # 等待并填写登录信息
            login_button_xpath = '//*[@id="site-content"]/div[2]/div/div/div[1]/form/div/div/div[1]/button[2]'
            page.click(login_button_xpath)
            page.fill('//*[@id=":r0:"]', email)  # 填写邮箱
            page.fill('//*[@id=":r1:"]', password)  # 填写密码
            page.click('//*[@id="site-content"]/div[2]/div/div/div[1]/form/div/div[4]/button[2]')  # 提交登录表单

            print("登录信息已提交。")
            time.sleep(10)  # 等待登录完成
            view_events='//*[@id="site-container"]/div/div[3]/div[3]/div[2]/button/div/span'

            page.click(view_events)
            time.sleep(10)
            gotit='//*[@id="site-content"]/div[1]/div/div[2]/div'
            if page.is_visible(gotit):
                page.click(gotit)
            select_button='//*[@id="kaggle-portal-root-global"]/div[2]/div[3]/div/ul[1]/li/div/div/div/button'
            page.click(select_button)
            stop_button='//*[@id="kaggle-portal-root-global"]/div[2]/div[3]/ul/li[2]'
            page.click(stop_button)
            print("实例已停止")
            page.goto("https://www.kaggle.com/")  # 返回主页准备退出登录
            account_button_xpath = '//*[@id="site-container"]/div/div[4]/div[2]/div[2]/div/div/div/div'
            confirm_button_xpath = '//*[@id="kaggle-portal-root-global"]/div/div[3]/div/div/ul[2]/div/li'
            page.click(account_button_xpath)
            time.sleep(1.5)
            page.click(confirm_button_xpath)
    except Exception as e:
        print(f"\033[91m失败：{str(e)}\033[0m")


def main():
    try:
        index=0
        accounts = data['kaggle_accounts']
        print(len(accounts))
        print("========== 启动完成 ==========")
        print("项目地址：https://github.com/avilliai/Achernar  点个star喵，点个star谢谢喵")
        while True:
            email, password = accounts[index]['email'], accounts[index]['password']
            print(f"========== 开始第 {index} 次运行，使用账户：{email} ==========")

            start_instance(email, password)
            #kill_instance(email, password)
            # 可选：在两次运行之间添加延时，避免过快执行
            time.sleep(data['kaggle_change_account_interval'])
            #kill_instance(email, password)
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

    # 创建一个 Session 对象，避免每次请求都重新登录
    session = requests.Session()

    def login(session, login_url, credentials):
        """ 登录函数，返回是否登录成功 """
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
        """ 获取隧道信息，返回最新的 tunnel_url """
        try:
            response = session.get(info_url)
            response.raise_for_status()

            if response.status_code == 200:
                tunnels=[]
                soup = BeautifulSoup(response.text, 'html.parser')
                table_rows = soup.select("table tbody tr")
                row = table_rows[-1] if table_rows else None
                if row:
                    columns = row.find_all("td")
                    if len(columns) > 0:
                        url_column = row.find("a")
                        newurl=url_column['href'] if url_column else "N/A"
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
        # 定时刷新获取隧道 URL
        new_tunnel_url = fetch_info_from_website(session, info_url)

        if new_tunnel_url!=None and new_tunnel_url!=[]:
            tunnel_url = new_tunnel_url
            print(f"最新隧道信息: {tunnel_url}")
        else:
            print("获取隧道信息失败，重新登录中...")
            # 如果获取链接失败，重新登录
            if not login(session, login_url, credentials):
                print("无法重新登录。")
                time.sleep(data['cpolar_check_interval'])
                continue
            new_tunnel_url = fetch_info_from_website(session, info_url)
            if new_tunnel_url!=[] and new_tunnel_url!=None:
                tunnel_url = new_tunnel_url
                print(f"最新隧道信息: {tunnel_url}")

        # 等待一段时间后再次获取
        time.sleep(data['cpolar_check_interval'])
def schedule_cpolar_main(): #cpolar定时任务
    cpolar_main()

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def proxy_request(path):
    global tunnel_url,url_index
    if not tunnel_url:
        return jsonify({"error": "隧道地址未初始化，请稍后再试"}), 503

    print(f"收到外部请求：{request.method} {request.url}")

    try:
        # 获取请求数据
        if request.method == 'GET':
            external_request = request.args.to_dict()
        else:
            external_request = request.get_json()
        if len(tunnel_url)==1:
            url_index=0

        current_url = tunnel_url[url_index]
        url_index = (url_index + 1) % len(tunnel_url)

        modified_tunnel_url = f"{current_url}/{path}"
        if request.query_string:
            modified_tunnel_url += f"?{request.query_string.decode('utf-8')}"

        print(f"转发至新的隧道地址：{modified_tunnel_url}")
        if data['quest_proxy'] is not None and data['quest_proxy'] != '':
            proxy = data['quest_proxy']
            proxies={"http": proxy, "https": proxy}
        else:
            proxies = None
        # 转发请求
        # 不要设置 Content-Type, 让 requests 自动处理
        headers = {key: value for key, value in request.headers.items() if key.lower() != 'host'}

        response = requests.request(request.method, modified_tunnel_url, params=request.args if request.method == 'GET' else None,
                                    json=external_request if request.method in ['POST', 'PUT', 'PATCH'] else None,
                                    data=request.get_data() if request.method not in ['GET', 'POST', 'PUT', 'PATCH'] else None,
                                    headers=headers, stream=True,proxies=proxies)

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
