
# Achernar
[Achernar命名的由来](https://www.star-facts.com/achernar/)
# 简介
- 1.用kaggle部署ai绘画脚本(也可以运行任意其他脚本)，自动切换账号
- 2.使用cpolar让ai绘画api实现内穿
- 3.使用flask在本地作为反向代理，自动刷新cpolar隧道链接。

综上，本项目可以使你在通过请求本地flask_api，调用部署在kaggle的ai绘画服务，而无需频繁地进入cpolar网站查询你的代理隧道。

同时，使用playwright，在多个kaggle账号间切换，实现持久化的ai绘画服务。
# kaggle白嫖ai绘画
下面的教程将带你实现白嫖kaggle的gpu资源。  
## kaggle注册登录  
[kaggle](https://www.kaggle.com/code/spawnerqwq/qqbot-simple-reforge-spawner)  
  
记得`在profile界面`  **绑定手机号**，不然用不了gpu和联网。  
## kaggle脚本修改(二选一)
二选一(建议用旧版脚本，双卡脚本的适配工作目前并未完成。)  
  
[双卡脚本](https://www.kaggle.com/code/spawnerqwq/qqbot-simple-reforge-spawner) 【速度】快，双卡并用榨干kaggle，均衡负载，出图较快。  
  
[旧版脚本](https://www.kaggle.com/code/lzrea06/qqbot-simple-reforge-spawner-bfef6d) 【稳定】，默认加载模型绘图效果好，出图较慢。  
### 使用frp
免费frp有很多，以[chml]([ChmlFrp | Panel v2 - 免费,高速,稳定,不限流量的端口映射工具。](https://panel.chmlfrp.cn/tunnelm/manage))为例。在他的官网注册登录，并完成实名验证。
![fc8578c69e33882d300b258902051516.png](https://raw.githubusercontent.com/avilliai/imgBed/master/images/fc8578c69e33882d300b258902051516.png)
![image.png](https://raw.githubusercontent.com/avilliai/imgBed/master/images/20250126101517.png)

![image.png](https://raw.githubusercontent.com/avilliai/imgBed/master/images/20250126101914.png)
好的，你现在得到了frp配置文件，它看起来如上图，让我们回到kaggle。

打开【脚本】后，点击白色的copy&edit，跳转到新页面后往下划拉。  
![image.png](https://raw.githubusercontent.com/avilliai/imgBed/master/images/20250126102141.png)
用你刚刚复制的配置文件内容替换掉这一坨。

让我们回到chml，**在【隧道列表】记录【连接地址】**
![image.png](https://raw.githubusercontent.com/avilliai/imgBed/master/images/20250126102449.png)
你得到了类似下面这样的连接地址
```yaml
hb.fuck.you:114514 
```
那我们就**记录**下面的内容。
```yaml
http://hb.fuck.you:114514  #加上了http://
```
### 使用cpolar
去[cpolar](https://dashboard.cpolar.com/get-started)注册(选免费套餐)，然后点验证，复制你的隧道 Authtoken ，比如`YTMgojjgnagtnbvjppf`(这是我乱打的，你并不能偷懒直接拿去用)  
  
打开【脚本】后，点击白色的copy&edit，跳转到新页面后往下划拉。  
![kaggle.png](https://raw.githubusercontent.com/avilliai/imgBed/master/images/kaggle.png)

把图中的`cpolar密钥`换成你上面申请的隧道AuthToken，看起来应该是这样  
```python  
cpolar_use = False
if cpolar_use:
    !curl -L https://www.cpolar.com/static/downloads/install-release-cpolar.sh | sudo bash
    !cpolar version
    !cpolar authtoken Y2IyNsdfafsaFUIHGGUAHOFMxYmE0
    def iframe_thread_1():
        !cpolar http 7860    #网页
    t1=threading.Thread(target=iframe_thread_1)
    t1.start()
    !wget -q -O - ipv4.icanhazip.com
    author = 'spawner'
```  
## 设为公开脚本  
点击页面右上角的share，将脚本设置为公开，这是为了其他账号能够正常访问。  
![kaggle1.png](https://raw.githubusercontent.com/avilliai/imgBed/master/images/kaggle1.png)

**记录下这里的public url**，然后点击save。  
```yaml  
https://www.kaggle.com/code/xxxx/qqbot-simple-reforge-spawner  
```  
这个【分享链接】我们待会会用到。  
## 更多备用账号
注册更多账号，记录好账号密码。  
  
**你注册的所有账号都需要能够通过 email+密码 登录，并且完成了手机号验证**  
  
验证码部分你可以找[接码平台](https://sms-activate.guru/en/email-activations)。  
  
**这些账号注册后，只要完成手机号验证就好了，不用别的操作。**  
## 部署Achernar  
[Achernar](https://github.com/avilliai/Achernar)  
  
### 拉取项目源码
```
git clone https://github.com/avilliai/Achernar
或使用镜像源  
git clone --depth 1 https://mirror.ghproxy.com/https://github.com/avilliai/Achernar
其他镜像源(推荐)  
git clone --depth 1 https://github.moeyy.xyz/https://github.com/avilliai/Achernar
```
不会用git自己看[avilliai/Achernar: kaggle账号自动切换+运行项目/cpolar隧道本地反向代理](https://github.com/avilliai/Achernar)有个绿色按钮，点了下载zip压缩包。
### 安装python
[安装python3.11](https://mirrors.huaweicloud.com/python/3.11.0/python-3.11.0-amd64.exe)

记住第一步勾选add to path就行了，剩下全默认。
### 安装依赖
运行`一键部署脚本.bat`
  
### 编辑Achernar配置文件  
`Achernar/config.yaml`  
```yaml  
#下面这两个代理项，一般不用配置。代理软件开规则代理完全够用。  
proxy: ""     #登录kaggle时使用的代理。  
quest_proxy: ""  #sd api请求时使用的代理地址，如果开启代理后，Achernar反代不能正常工作请填写此项。你代理软件的http代理地址。取决于具体情况，clash一般http://127.0.0.1:7890  
port: 3529  
headless: true   #是否开启浏览器无头模式，低配服务器建议开启。  
#在shared_notebook填入记录的你的【分享链接】  
shared_notebook: ""  
enable_kaggle_extension: true  
enable_cpolar_extension: true    #使用frp就将这个改成false
cpolar_check_interval: 180  
kaggle_change_account_interval: 39600  
  
kaggle_accounts:  
  - email: "你的邮箱"  
    password: "你的密码"  
  - email: "你的第二个邮箱"  
    password: "你的第二个密码"  #以此类推  
cpolar:                  #使用frp不用填
  email: "cpolar的邮箱"  
  password: "cpolar的密码"  
  
  
```  
**运行Achernar主程序**  
  
(有条件的话，建议开启代理，并设置为pac模式/规则代理模式，将有助于稳定运行。)  
# 调用
## 用Eridanus对接
[Eridanus对接Achernar](https://eridanus-doc.netlify.app/docs/%E6%8B%93%E5%B1%95%E5%8A%9F%E8%83%BD/ai%E7%BB%98%E7%94%BB/#kaggle%E9%83%A8%E7%BD%B2ai%E7%BB%98%E7%94%BB%E5%BF%85%E7%9C%8B)
## 自行编写代码对接
如使用cpolar，请求地址则为http://127.0.0.1:3529，如使用frp，请求地址则为你记录的【http://连接地址】(比如http://hb.fuck.you:114514)

```
payload = {
        "denoising_strength": 0.5,
        "enable_hr": 'false',
        "hr_scale": 1.5,
        "hr_second_pass_steps" : 15,
        "hr_upscaler" : 'SwinIR_4x',
        "prompt": f'score_9,score_8_up,score_7_up,{prompt},masterpiece,best quality,amazing quality,very aesthetic,absurdres,newest,',
        "negative_prompt": '((nsfw)),score_6,score_5,score_4,((furry)),lowres,(bad quality,worst quality:1.2),bad anatomy,sketch,jpeg artifacts,ugly, poorly drawn,(censor),blurry,watermark,simple background,transparent background',
        "seed": -1,
        "batch_size": 1,
        "n_iter": 1,
        "steps": 35,
        "cfg_scale": 6.5,
        "width": width,
        "height": height,
        "restore_faces": False,
        "tiling": False,
        "sampler_name": 'Euler a',
        "scheduler": 'Align Your Steps',
        "clip_skip_steps": 2,
        "override_settings": {
            "CLIP_stop_at_last_layers": 2,
            "sd_model_checkpoint": ckpt,  # 指定大模型
            },
        "override_settings_restore_afterwards": False,
    }  #manba out

async with httpx.AsyncClient(timeout=None) as client:
    response = await client.post(url='http://127.0.0.1:3529/sdapi/v1/txt2img', json=payload)
r = response.json()
```
# 鸣谢
[spawner](https://github.com/spawner1145) 提供了Achernar的账号切换脚本原型，以及编写了优秀的kaggle脚本。
