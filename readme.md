
# Achernar

[Achernar](https://www.star-facts.com/achernar/)

项目Eridanus的第一个派生项目
# 简介
- 1.用kaggle部署ai绘画脚本，自动切换账号
- 2.使用cpolar调用ai绘画api
- 3.使用flask在本地部署反向代理，自动刷新cpolar代理链接。

综上，本项目可以使你在通过请求本地flask_api，调用部署在kaggle的ai绘画服务，而无需频繁地进入cpolar网站查询你的代理隧道。

同时，使用selenium，在多个kaggle账号间切换，实现持久化的ai绘画服务。