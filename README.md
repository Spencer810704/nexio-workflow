Table of contents
- [介紹](#介紹)
- [安裝](#安裝)
  - [配置範例及各項用途說明](#配置範例及各項用途說明)
- [執行及驗證](#執行及驗證)

# 介紹
因我司每週都會有新的客戶需要建立相應VM以及初始化設置 以及 舊客戶站點下線, 此專案使用 Jenkins Pipeline 串接相應自動化工具

建立站點
- 觸發 Terraform 建立 VM
- 觸發 AWX 服務進行 server 的 initialize 
- 建立 Kibana index
- 新增客戶站點的 nginx vhost & reload nginx

刪除站點
- 移除CDN相關配置
- 移除PORTAL相關資訊
- 移除內部DNS資訊

<br>
