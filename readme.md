
# Achernar
[Eridanus](https://github.com/avilliai/Eridanus)衍生项目。
# 简介
- 1.自动运行公开kaggle脚本，在运行一定时长后自动切换账号并重新运行脚本。
- 2.使用flask在本地作为反向代理，自动刷新cpolar隧道链接。(使用frp固定节点时用不到这个。)
# 部署  

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
proxy: ""        #浏览器使用的代理
quest_proxy: ""  #反代请求时使用的代理地址，如果开启代理后，Achernar反代不能正常工作请填写此项。你代理软件的http代理地址。
port: 3529
shared_notebook: "dania-fix.ipynb"    #ipynb文件下载到本地，放到根目录
enable_kaggle_extension: true
enable_cpolar_extension: true
enable_get_dynamic_ip: false   #你一般用不到，这是个人提供的frp服务。不可与cpolar同时开启
cpolar_check_interval: 180
kaggle_change_account_interval: 43050

kaggle_accounts:
  - username: "方便你自己记的账户名"
    key: "KGAT_xxxxxx"
  - username: "方便你自己记的账户名"
    key: "KGAT_xxxxxx"
cpolar:
  email: "cpolar的邮箱"
  password: "cpolar的密码"
get_dynamic_ip:   #通过url获取动态ip
  url: ""
  port1: 11111
  port2: 22222

```  
**运行Achernar主程序/启动脚本.bat**  
  
建议开启代理，并设置为pac模式/规则代理模式，将有助于稳定运行。    
如遇连接失败    
- 1.确保kaggle脚本已运行，且cpolar/frp服务正常运行(可以打开连接地址)    
- 2.开启规则代理，将cpolar/frp域名连接规则设置为直连。如使用cpolar，由于二级域名不固定，建议用域名keywords即cpolar关键字匹配    

以clash配置文件为例，为规则代理添加以下两条规则    
```
rules:
  - DOMAIN-KEYWORD,cpolar,DIRECT
  - DOMAIN-KEYWORD,frp,DIRECT
```

