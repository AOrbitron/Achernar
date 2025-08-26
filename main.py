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
import re
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# 加载账户信息

with open('config.yaml', 'r', encoding='utf-8') as f:
    data = yaml.load(f.read(), Loader=yaml.FullLoader)

app = Flask(__name__)

# 全局变量，存储最新的隧道地址
tunnel_url = []
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
            if proxy != None and proxy != '' and proxy != "":  # 如果 proxy 不为空
                launch_args["proxy"] = {
                    "server": proxy
                }
                print(f"使用代理 {proxy}")

            browser = p.chromium.launch(**launch_args)
            context = browser.new_context()

            # 打开新的页面
            page = context.new_page()

            # 访问登录页面
            page.goto("https://www.kaggle.com/account/login", timeout=900000)
            print(f"尝试登录账户 {email}")

            # 等待并填写登录信息
            login_button_xpath = '//*[@id="site-content"]/div[2]/div/div/div[1]/form/div/div/div[1]/button[2]'
            page.click(login_button_xpath)

            def fill_email_field(email_value):
                selectors = [
                    # 通过name属性定位
                    'input[name="email"]',
                    # 通过placeholder定位
                    'input[placeholder*="email"]',
                    'input[placeholder*="Email"]',
                    'input[placeholder*="username"]',
                    # 通过aria-label定位
                    'input[aria-label*="email"]',
                    'input[aria-label*="Email"]',
                    # 通过type和autocomplete属性组合定位
                    'input[type="text"][autocomplete="on"]',
                    # 通过父元素的label文本定位
                    'label:has-text("Email") + div input, label:has-text("Email") >> .. >> input',
                    # 通过MUI类名定位第一个输入框
                    '.MuiTextField-root:first-of-type input',
                ]

                for selector in selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.fill(selector, email_value)
                            print(f"邮箱填写成功，使用选择器: {selector}")
                            return True
                    except Exception as e:
                        continue
                return False

            def fill_password_field(password_value):
                selectors = [
                    # 通过name属性定位
                    'input[name="password"]',
                    # 通过type定位
                    'input[type="password"]',
                    # 通过placeholder定位
                    'input[placeholder*="password"]',
                    'input[placeholder*="Password"]',
                    # 通过aria-label定位
                    'input[aria-label*="password"]',
                    'input[aria-label*="Password"]',
                    # 通过autocomplete属性定位
                    'input[autocomplete="current-password"]',
                    # 通过父元素的label文本定位
                    'label:has-text("Password") + div input, label:has-text("Password") >> .. >> input',
                ]

                for selector in selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.fill(selector, password_value)
                            print(f"密码填写成功，使用选择器: {selector}")
                            return True
                    except Exception as e:
                        continue
                return False

            if not fill_email_field(email):
                print("警告: 无法定位到邮箱输入框")
                try:
                    page.fill('//*[@id=":r0:"]', email)
                    print("使用原始XPath填写邮箱成功")
                except:
                    print("原始XPath也失效了")

            if not fill_password_field(password):
                print("警告: 无法定位到密码输入框")
                try:
                    page.fill('//*[@id=":r1:"]', password)
                    print("使用原始XPath填写密码成功")
                except:
                    print("原始XPath也失效了")
            page.click('//*[@id="site-content"]/div[2]/div/div/div[1]/form/div/div[4]/button[2]')  # 提交登录表单

            print("登录信息已提交。")
            time.sleep(8)  # 等待登录完成

            # 访问目标页面
            page.goto(data["shared_notebook"], timeout=900000)  # 替换成目标页面的URL
            print("尝试运行项目")

            # 尝试运行项目
            time.sleep(10)  # 等待项目加载完成
            if find_and_click(page, "Copy & Edit"):
                print("kaggle要求二次点击，点击Edit in Kaggle Notebooks")
                if not find_and_click(page, "Edit in Kaggle Notebooks"):
                    twice_buttons = ["/html/body/div[3]/div[3]/li[1]/div"]
                    for twi in twice_buttons:
                        try:
                            page.wait_for_selector(twi, state="visible",
                                                   timeout=30000)  # 使用wait_for_selector替换is_visable
                            page.click(twi)
                            print("已选择kaggle")
                            break
                        except Exception as e:
                            print(f"尝试点击 {twi} 失败: 尝试使用其他xpath路径定位")
            else:
                if find_and_click(page, "Edit My Copy"):
                    pass
                else:
                    page.wait_for_selector('//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/a/button',
                                           state="visible", timeout=30000)
                    page.click('//*[@id="site-content"]/div[2]/div/div/div[2]/div[1]/div/a/button')

                    # find_and_click(page,"Edit")
            print("等待页面加载完成")
            
            # 使用新的 Markdown 检测策略
            markdown_detected = False
            print("开始检测 Markdown 元素...")
            
            # 多种 Markdown 检测方法
            markdown_methods = [
                # 方法1: 直接检测 Markdown 相关元素
                lambda: page.locator("button").filter(has_text="Markdown").wait_for(state="visible", timeout=15000),
                # 方法2: 检测包含 markdown 文本的任意元素
                lambda: page.locator("//*[contains(text(), 'Markdown')]").wait_for(state="visible", timeout=15000),
                # 方法3: 检测代码编辑器相关元素
                lambda: page.locator(".monaco-editor, .code-editor, [data-testid*='editor']").wait_for(state="visible", timeout=15000),
                # 方法4: 检测页面加载状态指示器
                lambda: page.locator("[data-testid*='loading']").wait_for(state="hidden", timeout=15000),
                # 方法5: 等待页面网络空闲
                lambda: page.wait_for_load_state("networkidle", timeout=15000),
            ]
            
            for i, method in enumerate(markdown_methods, 1):
                try:
                    print(f"尝试 Markdown 检测方法 {i}")
                    method()
                    print(f"✅ Markdown 检测方法 {i} 成功")
                    markdown_detected = True
                    break
                except Exception as e:
                    print(f"Markdown 检测方法 {i} 失败")
                    continue
            
            if not markdown_detected:
                print("⚠️ 所有 Markdown 检测方法都失败，等待额外时间后继续...")
                time.sleep(10)
            
            # 新的 Save Version 点击策略
            print("尝试点击 Save Version")
            save_version_success = False
            
            # 多种 Save Version 点击方法
            save_version_methods = [
                # 方法1: 使用新的定位器策略
                lambda: page.locator("button").filter(has_text="Save Version").first.click(timeout=10000),
                # 方法2: 使用文本包含匹配
                lambda: page.locator("//button[contains(text(), 'Save Version')]").first.click(timeout=10000),
                # 方法3: 更宽泛的文本匹配
                lambda: page.locator("//*[contains(text(), 'Save Version')]").first.click(timeout=10000),
                # 方法4: 使用 get_by_role
                lambda: page.get_by_role("button", name=re.compile("Save Version", re.IGNORECASE)).click(timeout=10000),
                # 方法5: 查找所有按钮并过滤
                lambda: page.locator("button").filter(has_text=re.compile("Save Version", re.IGNORECASE)).first.click(timeout=10000),
            ]
            
            for i, method in enumerate(save_version_methods, 1):
                try:
                    print(f"尝试 Save Version 方法 {i}")
                    method()
                    print(f"✅ Save Version 点击成功 (方法 {i})")
                    save_version_success = True
                    break
                except Exception as e:
                    print(f"Save Version 方法 {i} 失败: {e}")
                    continue
            
            # 如果新方法都失败，使用原始 XPath 策略
            if not save_version_success:
                print("新 Save Version 策略失效，采用原始 XPath 方案")
                save_version_buttons = [
                    '//*[@id="site-content"]/div[2]/div/div[1]/div/div/div[4]/div[1]/button',
                    '//*[@id="site-content"]/div[2]/div[2]/div/div[1]/div/div/div[4]/div[1]/button',
                    '//*[@id="site-content"]/div[3]/div/div[1]/div/div/div[4]/div[1]/button',
                    '//*[@id="site-content"]/div[2]/div/div[1]/div/div/div[4]/span[1]/div/button',
                    # 添加更多可能的 XPath
                    "//button[contains(@class, 'save') or contains(@title, 'Save')]",
                    "//*[contains(@class, 'toolbar') or contains(@class, 'header')]//button[contains(text(), 'Save')]",
                ]
                
                time.sleep(7)
                
                # 先尝试改进的 save_version 函数
                save_version_function_methods = [
                    lambda: page.get_by_role("button", name=re.compile("Save Version", re.IGNORECASE)).click(timeout=30000),
                    lambda: page.locator("button").filter(has_text=re.compile("Save Version", re.IGNORECASE)).click(timeout=30000),
                    lambda: page.locator("//button[contains(text(), 'Save Version')]").click(timeout=30000),
                    lambda: page.locator("//*[contains(text(), 'Save Version')]").click(timeout=30000),
                ]
                
                for i, method in enumerate(save_version_function_methods, 1):
                    try:
                        print(f"尝试改进的 save_version 方法 {i}")
                        method()
                        print(f"✅ save_version 成功 (改进方法 {i})")
                        save_version_success = True
                        break
                    except Exception as e:
                        print(f"改进的 save_version 方法 {i} 失败: {e}")
                        continue
                
                # 最后使用原始 XPath
                if not save_version_success:
                    for save_version_button in save_version_buttons:
                        try:
                            element = page.locator(save_version_button)
                            if element.count() > 0:
                                element.wait_for(state="visible", timeout=30000)
                                element.click(timeout=30000)
                                print(f"✅ 已保存版本 (XPath: {save_version_button})")
                                save_version_success = True
                                break
                        except Exception as e:
                            print(f"尝试点击 {save_version_button} 失败: {e}")
                            continue

            time.sleep(8)
            
            # 新的确认按钮点击策略  
            print("尝试点击确认/保存按钮")
            confirm_success = False
            
            # 多种确认按钮点击方法
            confirm_methods = [
                # 方法1: Save 按钮
                lambda: page.locator("button").filter(has_text="Save").first.click(timeout=10000),
                # 方法2: Run 按钮
                lambda: page.locator("button").filter(has_text="Run").first.click(timeout=10000),
                # 方法3: Save & Run 按钮
                lambda: page.locator("button").filter(has_text=re.compile("Save.*Run|Run.*Save", re.IGNORECASE)).first.click(timeout=10000),
                # 方法4: 模态框中的 Save 按钮
                lambda: page.locator("[role='dialog'] button, .modal button").filter(has_text="Save").first.click(timeout=10000),
                # 方法5: 任何包含 Save 或 Run 的按钮
                lambda: page.locator("//button[contains(text(), 'Save') or contains(text(), 'Run')]").first.click(timeout=10000),
                # 方法6: 使用 get_by_role
                lambda: page.get_by_role("button", name=re.compile("Save|Run", re.IGNORECASE)).first.click(timeout=10000),
            ]
            
            for i, method in enumerate(confirm_methods, 1):
                try:
                    print(f"尝试确认按钮方法 {i}")
                    method()
                    print(f"✅ 确认按钮点击成功 (方法 {i})")
                    confirm_success = True
                    break
                except Exception as e:
                    print(f"确认按钮方法 {i} 失败: {e}")
                    continue
            
            # 如果新方法都失败，使用原始策略
            if not confirm_success:
                print("新确认策略失效，采用原始方案")
                confirm_buttons = [
                    '//*[@id="kaggle-portal-root-global"]/div/div[3]/div/div/div[4]/div[2]/button[2]',
                    '/html/body/div[2]/div[3]/div/div/div[4]/div[2]/button[2]',
                    '//*[@id="kaggle-portal-root-global"]/div[2]/div[3]/div/div/div[4]/div[2]/button[2]',
                    "//button[contains(., 'Save')]",
                    "button:has-text('Save')", 
                    "/html/body/div[contains(@class,'MuiDrawer-root') and contains(@class,'MuiDrawer-modal')]/div[contains(@class,'MuiDrawer-paper')]/div/div/div[last()]/div[last()]/button[last()]",
                    # 添加更多可能的选择器
                    "//div[contains(@class, 'modal') or contains(@class, 'dialog')]//button[contains(text(), 'Save') or contains(text(), 'Run')]",
                    "//*[@role='dialog']//button[contains(text(), 'Save') or contains(text(), 'Run')]",
                ]
                
                # 先尝试改进的 save 函数方法
                save_function_methods = [
                    lambda: page.get_by_role("button", name=re.compile("Save|Run", re.IGNORECASE)).click(timeout=30000),
                    lambda: page.locator("button").filter(has_text=re.compile("Save|Run", re.IGNORECASE)).click(timeout=30000),
                    lambda: page.locator("//button[contains(text(), 'Save') or contains(text(), 'Run')]").click(timeout=30000),
                    lambda: page.locator("//*[contains(text(), 'Save') or contains(text(), 'Run')]").click(timeout=30000),
                ]
                
                for i, method in enumerate(save_function_methods, 1):
                    try:
                        print(f"尝试改进的 save 方法 {i}")
                        method()
                        print(f"✅ save 成功 (改进方法 {i})")
                        confirm_success = True
                        break
                    except Exception as e:
                        print(f"改进的 save 方法 {i} 失败: {e}")
                        continue
                
                # 最后使用原始选择器
                if not confirm_success:
                    for confirm_button in confirm_buttons:
                        try:
                            element = page.locator(confirm_button)
                            if element.count() > 0:
                                element.wait_for(state="visible", timeout=30000)
                                element.click(timeout=30000)
                                print(f"✅ 已确认运行 (选择器: {confirm_button})")
                                confirm_success = True
                                break
                        except Exception as e:
                            print(f"尝试点击 {confirm_button} 失败: {e}")
                            continue
            
            if save_version_success and confirm_success:
                print("✅ 所有操作完成成功")
            elif save_version_success:
                print("⚠️ Save Version 成功，但确认操作可能失败")  
            elif confirm_success:
                print("⚠️ 确认操作成功，但 Save Version 可能失败")
            else:
                print("❌ 所有操作都可能失败，但继续执行...")
            
            print("run")
            time.sleep(5)
            print("项目运行中...")
            page.goto("https://www.kaggle.com/", timeout=900000)  # 返回主页准备退出登录



    except Exception as e:
        print(f"\033[91m任务失败：{str(e)}，重新尝试\033[0m")
        if browser:
            try:
                browser.close()
            except Exception as e:
                print(f"{str(e)}")
        start_instance(email, password)
    finally:

        if browser:
            print("任务完成，浏览器将关闭")
            try:
                browser.close()
            except Exception as e:
                print(f"{str(e)}")


def find_and_click(page, text, timeout=30000):
    """
    在页面中查找任意包含指定文本的元素并点击。
    """

    strategies = [
        lambda: page.get_by_role("button", name=text),
        lambda: page.get_by_title(text),
        lambda: page.get_by_label(text),
        lambda: page.locator(f"//button[@title='{text}']"),
        lambda: page.locator(f"//button[text()='{text}']"),
        lambda: page.locator(f"text=\"{text}\""),
        lambda: page.locator(f"//*[contains(text(), '{text}')]"),  # 通用查找
    ]

    for strategy in strategies:
        try:
            locator = strategy()
            if locator.count() == 0:
                continue
            locator.first.click(timeout=timeout)
            print(f"已点击包含文本 “{text}” 的元素")
            return True
        except PlaywrightTimeoutError:
            print(f"error：无法点击包含文本 “{text}” {e}")
            continue
        except Exception as e:
            continue

    print(f"❌ 无法点击文本 “{text}”，未找到匹配元素")
    return False


def save_version(page):
    try:
        # 推荐方法：使用 get_by_role 和 title
        page.get_by_role("button", name="Save Version").click(timeout=30000)
        print("已点击 Save Version 按钮 (使用 get_by_role 和 title)")
        return True
    except Exception as e:
        print(f"点击 Save Version 按钮失败: {e}")
        # 其他备选方案 (可选)
        try:
            page.get_by_title("Save Version").click(timeout=30000)
            print("已点击 Save Version 按钮 (使用 get_by_title)")
            return True
        except Exception as e:
            print(f"点击 Save Version 按钮失败: {e}")

        try:
            page.get_by_label("Save Version").click(timeout=30000)
            print("已点击 Save Version 按钮 (使用 get_by_label)")
            return True
        except Exception as e:
            print(f"点击 Save Version 按钮失败: {e}")

        try:
            page.locator("//button[@title='Save Version']").click(timeout=30000)
            print("已点击 Save Version 按钮 (使用 XPath)")
            return True
        except Exception as e:
            print(f"点击 Save Version 按钮失败: {e}")
        return False


def save(page):
    try:
        # 推荐方法：使用 get_by_role 和 name
        page.get_by_role("button", name="Save").click(timeout=30000)
        print("已点击 Save 按钮 (使用 get_by_role 和 name)")
        return True
    except Exception as e:
        print(f"点击 Save 按钮失败: {e}")

        # 其他备选方案 (可选)
        try:
            page.get_by_text("Save").click()
            print("已点击 Save 按钮 (使用 get_by_text)")
            return True
        except Exception as e:
            print(f"点击 Save 按钮失败: {e}")

        try:
            page.locator("button:has-text('Save')").click(timeout=30000)
            print("已点击 Save 按钮 (使用 CSS 选择器)")
            return True
        except Exception as e:
            print(f"点击 Save 按钮失败: {e}")

        try:
            page.locator("//button[contains(., 'Save')]").click(timeout=30000)
            print("已点击 Save 按钮 (使用 XPath)")
            return True
        except Exception as e:
            print(f"点击 Save 按钮失败: {e}")
        return False


def main():
    try:
        index = 0
        accounts = data['kaggle_accounts']
        print(len(accounts))
        print("========== 启动完成 ==========")
        print("项目地址：https://github.com/avilliai/Achernar  点个star喵，点个star谢谢喵")
        while True:
            email, password = accounts[index]['email'], accounts[index]['password']
            print(f"========== 开始第 {index} 次运行，使用账户：{email} ==========")

            start_instance(email, password)
            # kill_instance(email, password)
            # 可选：在两次运行之间添加延时，避免过快执行
            time.sleep(data['kaggle_change_account_interval'])
            # kill_instance(email, password)
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
        # 定时刷新获取隧道 URL
        new_tunnel_url = fetch_info_from_website(session, info_url)

        if new_tunnel_url != None and new_tunnel_url != []:
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
            if new_tunnel_url != [] and new_tunnel_url != None:
                tunnel_url = new_tunnel_url
                print(f"最新隧道信息: {tunnel_url}")

        # 等待一段时间后再次获取
        time.sleep(data['cpolar_check_interval'])


def schedule_cpolar_main():  # cpolar定时任务
    cpolar_main()


def get_dynamic_ip():
    global tunnel_url
    get_ip_url = data["get_dynamic_ip"]["url"]

    def fetch_info_from_website():
        """ 获取隧道信息，返回最新的 tunnel_url """
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
        # 定时刷新获取隧道 URL
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

        # 等待一段时间后再次获取
        time.sleep(data['cpolar_check_interval'])


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def proxy_request(path):
    global tunnel_url, url_index
    if not tunnel_url:
        return jsonify({"error": "隧道地址未初始化，请稍后再试"}), 503

    print(f"收到外部请求：{request.method} {request.url}")

    try:
        # 获取请求数据
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
        if data['quest_proxy'] is not None and data['quest_proxy'] != '':
            proxy = data['quest_proxy']
            proxies = {"http": proxy, "https": proxy}
        else:
            proxies = None
        # 转发请求
        # 不要设置 Content-Type, 让 requests 自动处理
        headers = {key: value for key, value in request.headers.items() if key.lower() != 'host'}

        response = requests.request(request.method, modified_tunnel_url,
                                    params=request.args if request.method == 'GET' else None,
                                    json=external_request if request.method in ['POST', 'PUT', 'PATCH'] else None,
                                    data=request.get_data() if request.method not in ['GET', 'POST', 'PUT',
                                                                                      'PATCH'] else None,
                                    headers=headers, stream=True, proxies=proxies)

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
    if data["enable_get_dynamic_ip"]:
        threading.Thread(target=get_dynamic_ip, daemon=True).start()

    app.run(host='0.0.0.0', port=data['port'])
