
# Achernar
[Achernar命名的由来](https://www.star-facts.com/achernar/)
# 简介
- 1.用kaggle部署ai绘画脚本(也可以运行任意其他脚本)，自动切换账号
- 2.使用cpolar/frp让ai绘画api实现内穿
- 3.使用flask在本地作为反向代理，自动刷新cpolar隧道链接。

[教程](https://eridanus-doc.netlify.app/docs/lessons/kaggle%E9%83%A8%E7%BD%B2ai%E7%BB%98%E7%94%BB)
# 部署  
[Achernar](https://github.com/avilliai/Achernar)  
  
## 拉取项目源码
```
git clone https://github.com/avilliai/Achernar
或使用镜像源  
git clone --depth 1 https://mirror.ghproxy.com/https://github.com/avilliai/Achernar
其他镜像源(推荐)  
git clone --depth 1 https://github.moeyy.xyz/https://github.com/avilliai/Achernar
```
不会用git自己看右上角有个绿色按钮，点了下载zip压缩包。
## 安装python
[安装python3.11](https://mirrors.huaweicloud.com/python/3.11.0/python-3.11.0-amd64.exe)

记住第一步勾选add to path就行了，剩下全默认。
## 安装依赖
运行`一键部署脚本.bat`
  
## 编辑Achernar配置文件  
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
[Eridanus对接Achernar](https://eridanus-doc.netlify.app/docs/lessons/kaggle%E9%83%A8%E7%BD%B2ai%E7%BB%98%E7%94%BB)
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
