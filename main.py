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
target_urls = {}

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

            # 等待并点击编辑按钮
            edit_button_xpath = '//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/div[2]/div/span/a/button'

            if page.is_visible(edit_button_xpath):
                page.click(edit_button_xpath)
            print("已进入项目页")

            # 尝试运行项目
            time.sleep(10)  # 等待项目加载完成
            edit_b='//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/a/button'
            if page.is_visible(edit_b):
                page.click(edit_b)
                print("已进入编辑页")
            edit_c='//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/div[2]/span/a/button'
            if page.is_visible(edit_c):
                page.click(edit_c)
                print("已进入编辑页")
            edit_d='//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/div[2]/div/span/a/button'
            if page.is_visible(edit_d):
                page.click(edit_d)
                print("已进入编辑页")
            print("等待页面加载完成(25秒)")
            time.sleep(25)
            page.evaluate("""
                () => {
                    const blocker1 = document.querySelector('.sc-ftmehX.clyupM');
                    const blocker2 = document.querySelector('.MuiBackdrop-root');
                    if (blocker1) blocker1.style.pointerEvents = 'none';
                    if (blocker2) blocker2.style.pointerEvents = 'none';
                }
            """)
            save_version1= '//*[@id="site-content"]/div[3]/div/div[1]/div/div/div[4]/div[1]/button'
            if page.is_visible(save_version1):
                page.click(save_version1)
                print("版本已创建")
            else:
                save_version=  '//*[@id="site-content"]/div[2]/div[2]/div/div[1]/div/div/div[4]/div[1]/button'
                page.click(save_version,force=True,timeout=900000)
            print("版本已创建")

            time.sleep(10)
            confirm_button_xpath = '//*[@id="kaggle-portal-root-global"]/div/div[3]/div/div/div[4]/div[2]/button[2]'
            page.click(confirm_button_xpath)
            time.sleep(3)
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
        soup = BeautifulSoup(response.text, 'html.parser')

        excluded_links = [
            'https://www.cpolar.com/download',
            'https://www.cpolar.com/docs',
            'https://www.cpolar.com',
            'https://www.cpolar.com/2024end',
            'https://cpolar.com/tos',
            'https://cpolar.com/privacy'
        ]

        links = [
            a['href'] for a in soup.find_all('a', href=True)
            if 'https' in a['href'] and 'cpolar' in a['href'] and a['href'] not in excluded_links
        ]

        print(f"提取的所有链接: {links}")

        filtered_links = {
            f"/v{i}": link.replace("http://", "https://")
            for i, link in enumerate(links, start=0)
        }
        return filtered_links
    except Exception as e:
        print(f"获取隧道信息失败：{str(e)}")
        return {}

def proxy_request(target_host):
    def handler():
        headers = {
            key: value for key, value in request.headers.items() if key.lower() != 'host'
        }
        modified_tunnel_url = f"{target_host}{request.full_path[len(request.path):]}"
        proxies = {
            "http": data['quest_proxy'],
            "https": data['quest_proxy']
        } if data['quest_proxy'] else None

        response = requests.request(
            request.method,
            modified_tunnel_url,
            params=request.args,
            json=request.json if request.method in ['POST', 'PUT', 'PATCH'] else None,
            data=request.get_data() if request.method not in ['GET', 'POST', 'PUT', 'PATCH'] else None,
            headers=headers,
            stream=True,
            proxies=proxies
        )

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [
            (name, value) for (name, value) in response.headers.items()
            if name.lower() not in excluded_headers
        ]

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk

        return Response(generate(), response.status_code, headers)

    return handler

def update_routes():
    global target_urls

    app.url_map._rules.clear()
    app.url_map._rules_by_endpoint.clear()
    app.view_functions.clear()

    @app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
    def catch_all(path):
        return "未找到", 404

    for path, url in target_urls.items():
        app.add_url_rule(
            path + '/',
            defaults={'path': ''},
            view_func=proxy_request(url),
            endpoint=path + '_root',
            methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']
        )
        app.add_url_rule(
            path + '/<path:path>',
            view_func=proxy_request(url),
            endpoint=path + '_path',
            methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']
        )

    print(f"反向代理已配置: 访问 http://localhost:{data['port']}{path} 将被转发到 {url}")

def cpolar_main():
    global target_urls

    login_url = "https://dashboard.cpolar.com/login"
    info_url = "https://dashboard.cpolar.com/status"
    credentials = {
        'login': data["cpolar"]["email"],
        'password': data["cpolar"]["password"]
    }

    session = requests.Session()

    if login(session, login_url, credentials):
        while True:
            new_target_urls = fetch_info_from_website(session, info_url)
            if new_target_urls != target_urls:
                target_urls = new_target_urls
                print(f"最新目标URLs: {target_urls}")
                try:
                    update_routes()
                    print("已更新路由规则。")
                except Exception as e:
                    print(f"更新路由规则失败：{str(e)}")
            time.sleep(data['cpolar_check_interval'])
def schedule_cpolar_main(): #cpolar定时任务
    cpolar_main()




if __name__ == "__main__":
    if data["enable_cpolar_extension"]:
        threading.Thread(target=schedule_cpolar_main, daemon=True).start()
    if data["enable_kaggle_extension"]:
        threading.Thread(target=main, daemon=True).start()

    app.run(host='0.0.0.0', port=data['port'])
