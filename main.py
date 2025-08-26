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
            # ==================== 主要的替换代码 ====================
            
            print("等待页面加载完成")
            
            # 第一步：等待Markdown文本出现
            if not wait_for_text_to_appear(page, "Markdown", 120000):
                print("⚠️  Markdown文本未出现，但继续执行后续操作...")
            else:
                print("✅ Markdown文本已出现，页面加载完成")
            
            # 第二步：点击Save Version文本
            print("\\n开始点击Save Version...")
            if not click_text_with_retry(page, "Save Version", max_retries=3):
                print("⚠️  Save Version点击失败，尝试点击包含Save的文本...")
                # 备用方案：尝试点击任何包含"Save"的文本
                if not click_text_with_retry(page, "Save", max_retries=2):
                    print("❌ 所有保存相关的点击都失败了")
            else:
                print("✅ Save Version点击成功")
            
            # 等待保存对话框出现
            time.sleep(5)
            
            # 第三步：点击确认保存的Save按钮
            print("\\n开始点击确认保存...")
            # 在对话框中查找Save按钮，避免与之前的Save Version混淆
            if not click_text_with_retry(page, "Save", max_retries=3):
                print("❌ 确认保存点击失败")
            else:
                print("✅ 确认保存点击成功")
            
            print("\\n所有文本点击操作完成")
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
"""
目前没电脑用只有平板，靠ai了
"""
def find_and_click_text(page, target_text, timeout=60000):
    """
    在整个页面中搜索文本并直接点击，类似于Ctrl+F搜索
    Args:
        page: playwright页面对象
        target_text: 要搜索的目标文本
        timeout: 超时时间(毫秒)
    Returns:
        bool: 是否成功点击
    """
    print(f"在页面中搜索并点击文本: '{target_text}'")
    
    start_time = time.time() * 1000
    
    while (time.time() * 1000 - start_time) < timeout:
        try:
            # 等待页面稳定
            page.wait_for_load_state("networkidle", timeout=5000)
            
            # 使用JavaScript在整个页面中搜索文本并点击
            click_result = page.evaluate(f"""
                (targetText) => {{
                    // 创建一个TreeWalker来遍历所有文本节点
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let node;
                    const foundElements = [];
                    
                    // 遍历所有文本节点
                    while (node = walker.nextNode()) {{
                        const text = node.textContent;
                        if (text && text.includes(targetText)) {{
                            const parentElement = node.parentElement;
                            if (parentElement) {{
                                const rect = parentElement.getBoundingClientRect();
                                const isVisible = rect.width > 0 && rect.height > 0 && 
                                                rect.top >= 0 && rect.left >= 0 &&
                                                window.getComputedStyle(parentElement).visibility !== 'hidden' &&
                                                window.getComputedStyle(parentElement).display !== 'none';
                                
                                if (isVisible) {{
                                    foundElements.push({{
                                        element: parentElement,
                                        text: text.trim(),
                                        rect: rect
                                    }});
                                }}
                            }}
                        }}
                    }}
                    
                    // 如果找到了元素，点击第一个
                    if (foundElements.length > 0) {{
                        const targetElement = foundElements[0].element;
                        
                        // 滚动到元素位置
                        targetElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        
                        // 模拟鼠标点击
                        const clickEvent = new MouseEvent('click', {{
                            view: window,
                            bubbles: true,
                            cancelable: true
                        }});
                        
                        targetElement.dispatchEvent(clickEvent);
                        
                        // 也尝试直接调用click方法
                        if (targetElement.click) {{
                            targetElement.click();
                        }}
                        
                        return {{
                            success: true,
                            foundCount: foundElements.length,
                            clickedText: foundElements[0].text,
                            elementTag: targetElement.tagName,
                            elementClass: targetElement.className
                        }};
                    }}
                    
                    return {{
                        success: false,
                        foundCount: 0,
                        reason: 'No visible elements containing the text were found'
                    }};
                }}
            """, target_text)
            
            if click_result.get('success'):
                print(f"✅ 找到并点击了文本 '{target_text}'")
                print(f"   找到 {click_result['foundCount']} 个匹配元素")
                print(f"   点击的元素: {click_result['elementTag']} - '{click_result['clickedText'][:50]}...'")
                time.sleep(2)  # 等待点击生效
                return True
            else:
                print(f"未找到可点击的文本 '{target_text}': {click_result.get('reason', '未知原因')}")
                
        except Exception as e:
            print(f"搜索点击过程出错: {str(e)}")
        
        # 等待一段时间后重试
        elapsed_seconds = int((time.time() * 1000 - start_time) / 1000)
        if elapsed_seconds % 10 == 0:  # 每10秒打印一次
            print(f"继续搜索 '{target_text}'... (已等待 {elapsed_seconds}s)")
        
        time.sleep(2)
    
    print(f"❌ 搜索点击 '{target_text}' 超时失败")
    return False

def wait_for_text_to_appear(page, target_text, timeout=120000):
    """
    等待指定文本在页面中出现
    Args:
        page: playwright页面对象
        target_text: 要等待的文本
        timeout: 超时时间(毫秒)
    Returns:
        bool: 文本是否出现
    """
    print(f"等待文本 '{target_text}' 出现在页面中...")
    
    start_time = time.time() * 1000
    
    while (time.time() * 1000 - start_time) < timeout:
        try:
            # 使用JavaScript检查页面中是否包含目标文本
            text_found = page.evaluate(f"""
                (targetText) => {{
                    // 检查整个页面的文本内容
                    const bodyText = document.body.textContent || document.body.innerText || '';
                    return bodyText.includes(targetText);
                }}
            """, target_text)
            
            if text_found:
                print(f"✅ 文本 '{target_text}' 已出现在页面中")
                return True
                
        except Exception as e:
            print(f"检查文本时出错: {str(e)}")
        
        elapsed_seconds = int((time.time() * 1000 - start_time) / 1000)
        if elapsed_seconds % 15 == 0:  # 每15秒打印一次
            print(f"继续等待 '{target_text}'... (已等待 {elapsed_seconds}s)")
        
        time.sleep(3)
    
    print(f"❌ 等待文本 '{target_text}' 出现超时")
    return False

def click_text_with_retry(page, target_text, max_retries=3, timeout=30000):
    """
    重试点击文本
    """
    for attempt in range(max_retries):
        print(f"第 {attempt + 1} 次尝试点击 '{target_text}'")
        if find_and_click_text(page, target_text, timeout):
            return True
        if attempt < max_retries - 1:
            print(f"等待3秒后重试...")
            time.sleep(3)
    return False


"""
以上均为ai生成修复代码
"""

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
