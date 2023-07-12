# 開發環境
Python 版本: Python 3.9.2

# 建站流程

1. Provisioning (建立機器、設定IP、設定主機DNS)
2. Initialize (設定Hostname、安裝OS所需工具、新增SSH CA驗證、安裝Openresty、lua、OpenJDK等工具)
3. Generate_Internal_Nginx (Common Job , 用於產生內部服務溝通的 Nginx Virtual host) 
4. Reload_Internal_Nginx (Common Job) 
5. Register_Kibana_Index (註冊Kibana index)
6. Update_Nginx_Configuration (Common Job, 更新Nginx域名轉導層的Virtual host) 


# 目錄結構規範
在新增白牌的邏輯中 , 先透過不同的機房先進行命名已便分類 , 在該目錄下進行命名步驟 , 如
1_provisioning
2_initialize
3_register_kibana_index
以便清楚知道整個流程的順序性

# Common目錄
該目錄存放共用的函數 , 例如生成Internal Nginx配置、Reload Internal Nginx、更新目錄 , 這些Job目前都還是套用Chief機房 , 故將相同功能提取出至Common中


# 待辦事項
因Chief機房的資源緊缺 , 目前無打算再繼續新增白牌 , 故沒有寫相應的建置流程 , 如未來需要使用 , 則可參考FET機房建制步驟