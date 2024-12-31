
# Achernar

[Achernar](https://www.star-facts.com/achernar/)

项目Eridanus的第一个派生项目

[Eridanus对接Achernar](https://eridanus-doc.netlify.app/docs/%E6%8B%93%E5%B1%95%E5%8A%9F%E8%83%BD/ai%E7%BB%98%E7%94%BB/#kaggle%E9%83%A8%E7%BD%B2ai%E7%BB%98%E7%94%BB%E5%BF%85%E7%9C%8B)
# 简介
- 1.用kaggle部署ai绘画脚本，自动切换账号
- 2.使用cpolar让ai绘画api实现内穿
- 3.使用flask在本地部署反向代理，自动刷新cpolar隧道链接。

综上，本项目可以使你在通过请求本地flask_api，调用部署在kaggle的ai绘画服务，而无需频繁地进入cpolar网站查询你的代理隧道。

同时，使用selenium，在多个kaggle账号间切换，实现持久化的ai绘画服务。
# 部署
## 安装python
[安装python3.11](https://blog.csdn.net/MichaelJiangJunC/article/details/129996726)
## 安装依赖
运行`一键部署脚本.bat`
# 配置
```yaml
proxy: ""     #没用，不用管这一项
port: 3529   #项目运行的端口，可以记录一下
shared_notebook: ""           #你的共享笔记本的链接
enable_kaggle_extension: true
enable_cpolar_extension: true
cpolar_check_interval: 3600         #cpolar检查时间
kaggle_change_account_interval: 36000   #kaggle账号切换间隔

kaggle_accounts:
  - email: "你的kaggle账号"
    password: "密码"
  - email: "你的第二个kaggle账号"
    password: "密码"  #以此类推
cpolar:
  email: "你的cpolar账号"
  password: "密码"
```
**你可以直接向http://127.0.0.1:3529发送sd绘画请求，而无需再手动去cpolar记录代理隧道地址**。
```python
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