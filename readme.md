
# Achernar
[Eridanus](https://github.com/avilliai/Eridanus)衍生项目。
# 简介
- 1.自动运行kaggle脚本，在运行一定时长后自动切换账号并重新运行脚本。
- 2.使用flask在本地作为反向代理，自动刷新cpolar隧道链接。(使用frp用不到这个。)
# 部署  
[示例：部署ai绘画服务](https://eridanus-doc.netlify.app/docs/lessons/kaggle%E9%83%A8%E7%BD%B2ai%E7%BB%98%E7%94%BB)
  
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
headless: true   #浏览器无头模式  
#在shared_notebook填入公开脚本的【分享链接】  
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
**运行Achernar主程序/启动脚本.bat**  
  
(建议开启代理，并设置为pac模式/规则代理模式，将有助于稳定运行。
如遇连接失败
- 1.确保kaggle脚本已运行
- 2.开启规则代理，将cpolar/frp域名连接规则设置为直连。如使用cpolar，由于二级域名不固定，建议用域名keywords即cpolar关键字匹配

以clash配置文件为例，为规则代理添加以下两条规则
'''
rules:
  - DOMAIN-KEYWORD,cpolar,DIRECT
  - DOMAIN-KEYWORD,frp,DIRECT
'''
)
# 鸣谢
[spawner](https://github.com/spawner1145) 提供了Achernar的账号切换脚本原型，以及编写了优秀的kaggle脚本。
