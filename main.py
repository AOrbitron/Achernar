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
            
            # 先做全面的页面调试
            comprehensive_page_debug(page)
            
            # 1. 等待Markdown按钮
            print("\\n=== 第一步：等待Markdown按钮 ===")
            if not ultimate_element_finder(page, ['Markdown'], 'Markdown按钮检测', 120000):
                print("⚠️ Markdown按钮检测失败，但继续执行...")
            else:
                print("✅ Markdown按钮检测成功")
            
            # 2. 点击Save Version
            print("\\n=== 第二步：点击Save Version ===")
            if not ultimate_click_element(page, ['Save Version'], 'Save Version点击', 90000):
                print("⚠️ Save Version点击失败")
            else:
                print("✅ Save Version点击成功")
            
            # 等待弹窗出现
            time.sleep(5)
            
            # 3. 点击确认保存
            print("\\n=== 第三步：点击确认保存 ===")
            if not ultimate_click_element(page, ['Save'], '确认保存点击', 60000):
                print("⚠️ 确认保存点击失败")
            else:
                print("✅ 确认保存点击成功")
            
            print("\\n=== 所有操作完成 ===")
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
def ultimate_element_finder(page, target_texts, action_name, timeout=120000):
    """
    终极元素查找器 - 使用最底层的方法查找和点击元素
    Args:
        page: playwright页面对象
        target_texts: 目标文本列表 (如 ['Markdown', 'Save Version', 'Save'])
        action_name: 操作名称
        timeout: 超时时间(毫秒)
    Returns:
        bool: 是否找到目标元素
    """
    print(f"开始终极搜索: {action_name}")
    
    start_time = time.time() * 1000
    check_interval = 3000  # 3秒检查一次
    
    while (time.time() * 1000 - start_time) < timeout:
        try:
            # 等待页面基本稳定
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # 方法1: 使用JavaScript直接在页面中搜索
            found_element = page.evaluate(f"""
                () => {{
                    const targetTexts = {target_texts};
                    const results = [];
                    
                    // 获取所有可能的元素
                    const allElements = document.querySelectorAll('*');
                    
                    for (let element of allElements) {{
                        const text = (element.textContent || '').trim();
                        const innerText = (element.innerText || '').trim();
                        
                        for (let targetText of targetTexts) {{
                            if (text.includes(targetText) || innerText.includes(targetText)) {{
                                const rect = element.getBoundingClientRect();
                                const isVisible = rect.width > 0 && rect.height > 0 && 
                                                window.getComputedStyle(element).visibility !== 'hidden' &&
                                                window.getComputedStyle(element).display !== 'none';
                                
                                results.push({{
                                    tagName: element.tagName,
                                    text: text.substring(0, 100),
                                    innerText: innerText.substring(0, 100),
                                    className: element.className,
                                    id: element.id,
                                    isVisible: isVisible,
                                    isButton: element.tagName === 'BUTTON' || element.role === 'button',
                                    matchedText: targetText,
                                    rect: {{ x: rect.x, y: rect.y, width: rect.width, height: rect.height }}
                                }});
                            }}
                        }}
                    }}
                    
                    return results;
                }}
            """)
            
            if found_element and len(found_element) > 0:
                print(f"✅ JavaScript搜索找到 {len(found_element)} 个匹配元素:")
                
                # 打印找到的元素信息
                for i, elem in enumerate(found_element[:5]):  # 只显示前5个
                    print(f"  元素 {i+1}: {elem['tagName']} - '{elem['text'][:50]}' - 可见:{elem['isVisible']} - 按钮:{elem['isButton']}")
                
                # 优先选择可见的按钮元素
                clickable_elements = [e for e in found_element if e['isVisible'] and (e['isButton'] or e['tagName'] in ['BUTTON', 'A', 'DIV'])]
                
                if clickable_elements:
                    print(f"找到 {len(clickable_elements)} 个可点击元素")
                    return True
                else:
                    print("找到匹配元素但都不可点击")
            
            # 方法2: 检查iframe
            try:
                frames = page.frames
                if len(frames) > 1:
                    print(f"检测到 {len(frames)} 个frame，逐一检查...")
                    for frame in frames:
                        if frame != page.main_frame:
                            try:
                                frame_content = frame.content()
                                for target_text in target_texts:
                                    if target_text in frame_content:
                                        print(f"在iframe中找到 {target_text}")
                                        return True
                            except:
                                continue
            except Exception as e:
                pass
                
            elapsed_seconds = int((time.time() * 1000 - start_time) / 1000)
            print(f"继续搜索 {action_name}... (已等待 {elapsed_seconds}s)")
            time.sleep(check_interval / 1000)
            
        except Exception as e:
            print(f"搜索过程出错: {str(e)}")
            time.sleep(check_interval / 1000)
    
    print(f"❌ {action_name} 搜索超时")
    return False

def ultimate_click_element(page, target_texts, action_name, timeout=60000):
    """
    终极元素点击器
    """
    print(f"开始点击操作: {action_name}")
    
    start_time = time.time() * 1000
    
    while (time.time() * 1000 - start_time) < timeout:
        try:
            # 使用JavaScript查找并点击元素
            click_result = page.evaluate(f"""
                () => {{
                    const targetTexts = {target_texts};
                    
                    // 获取所有可能的可点击元素
                    const allElements = document.querySelectorAll('button, a, div[role="button"], span[role="button"], *[onclick]');
                    
                    for (let element of allElements) {{
                        const text = (element.textContent || '').trim();
                        const innerText = (element.innerText || '').trim();
                        
                        for (let targetText of targetTexts) {{
                            if (text.includes(targetText) || innerText.includes(targetText)) {{
                                const rect = element.getBoundingClientRect();
                                const isVisible = rect.width > 0 && rect.height > 0 && 
                                                window.getComputedStyle(element).visibility !== 'hidden' &&
                                                window.getComputedStyle(element).display !== 'none';
                                
                                if (isVisible) {{
                                    // 滚动到元素位置
                                    element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                    
                                    // 等待一下再点击
                                    setTimeout(() => {{
                                        element.click();
                                    }}, 500);
                                    
                                    return {{
                                        success: true,
                                        elementInfo: {{
                                            tagName: element.tagName,
                                            text: text.substring(0, 50),
                                            matchedText: targetText
                                        }}
                                    }};
                                }}
                            }}
                        }}
                    }}
                    
                    return {{ success: false, reason: 'No clickable element found' }};
                }}
            """)
            
            if click_result and click_result.get('success'):
                print(f"✅ {action_name} 点击成功!")
                print(f"   点击的元素: {click_result['elementInfo']['tagName']} - '{click_result['elementInfo']['text']}'")
                time.sleep(2)  # 等待点击生效
                return True
            else:
                print(f"点击尝试失败: {click_result.get('reason', '未知原因')}")
                
        except Exception as e:
            print(f"点击过程出错: {str(e)}")
        
        time.sleep(2)
        
        if (time.time() * 1000 - start_time) > timeout:
            break
    
    print(f"❌ {action_name} 点击失败")
    return False

def comprehensive_page_debug(page):
    """
    全面的页面调试信息
    """
    print("=== 全面页面调试信息 ===")
    try:
        # 页面基本信息
        url = page.url
        title = page.title()
        print(f"当前页面: {url}")
        print(f"页面标题: {title}")
        
        # 检查页面中的所有文本内容
        all_text = page.evaluate("""
            () => {
                const texts = [];
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let node;
                while (node = walker.nextNode()) {
                    const text = node.textContent.trim();
                    if (text.length > 0) {
                        texts.push(text);
                    }
                }
                return texts;
            }
        """)
        
        # 查找包含关键词的文本
        keywords = ['Markdown', 'Save', 'Version', 'Run']
        found_texts = []
        for text in all_text:
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    found_texts.append(f"'{text[:100]}...'")
                    break
        
        print(f"找到包含关键词的文本 ({len(found_texts)}个):")
        for text in found_texts[:10]:  # 只显示前10个
            print(f"  {text}")
        
        # 检查所有按钮
        buttons_info = page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button, a, div[role="button"], span[role="button"]');
                const results = [];
                
                buttons.forEach((btn, index) => {
                    if (index < 20) {  // 只检查前20个
                        const rect = btn.getBoundingClientRect();
                        const isVisible = rect.width > 0 && rect.height > 0;
                        
                        results.push({
                            index: index,
                            tagName: btn.tagName,
                            text: (btn.textContent || '').trim().substring(0, 50),
                            className: btn.className,
                            id: btn.id,
                            isVisible: isVisible
                        });
                    }
                });
                
                return results;
            }
        """)
        
        print(f"\\n页面中的按钮元素 ({len(buttons_info)}个):")
        for btn in buttons_info:
            print(f"  [{btn['index']}] {btn['tagName']} - '{btn['text']}' - 可见:{btn['isVisible']}")
        
    except Exception as e:
        print(f"调试信息获取失败: {str(e)}")
    
    print("=== 调试信息结束 ===\\n")


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
