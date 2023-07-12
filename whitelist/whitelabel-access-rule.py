import os
import json
import requests
import argparse
from rediscluster import RedisCluster

# 是方機房Redis
chief_redis_cluster_startup_nodes = [
    {"host": "redis01.mps", "port": 6379},
    {"host": "redis02.mps", "port": 6379},
    {"host": "redis03.mps", "port": 6379},
    {"host": "redis04.mps", "port": 6379},
    {"host": "redis05.mps", "port": 6379},
    {"host": "redis06.mps", "port": 6379},
]

# FET機房Redis
fet_redis_cluster_startup_nodes = [
    {"host": "fet-redis01.mps", "port": 6379},
    {"host": "fet-redis02.mps", "port": 6379},
    {"host": "fet-redis03.mps", "port": 6379},
    {"host": "fet-redis04.mps", "port": 6379},
    {"host": "fet-redis05.mps", "port": 6379},
    {"host": "fet-redis06.mps", "port": 6379},
]

# Azure Cloud Redis (非VM)
azure_redis_cluster_startup_nodes = [
    {"host": "10.128.2.4", "port": 6380}
]

# Azure Redis (6台VM)
azure_z01_redis_cluster_startup_nodes = [
    {"host": "azure-redis01.pf", "port": 6379},
    {"host": "azure-redis02.pf", "port": 6379},
    {"host": "azure-redis03.pf", "port": 6379},
    {"host": "azure-redis04.pf", "port": 6379},
    {"host": "azure-redis05.pf", "port": 6379},
    {"host": "azure-redis06.pf", "port": 6379},
]

#azure_wjp_cluster_startup_nodes = [
#    {"host": "azure-wjp-redis01.mps", "port": 6379},
#    {"host": "azure-wjp-redis02.mps", "port": 6379},
#    {"host": "azure-wjp-redis03.mps", "port": 6379},
#    {"host": "azure-wjp-redis04.mps", "port": 6379},
#    {"host": "azure-wjp-redis05.mps", "port": 6379},
#    {"host": "azure-wjp-redis06.mps", "port": 6379},
#]


def check_record_exist(wl_id:str, wl_code:str, fe_type:str) -> bool:
    """
    檢查Devops-Portal是否存在指定白牌的黑白名單及地區限制資料

    Args:
        wl_id (str): 白牌ID
        wl_code (str): 白牌Code
        fe_type (str): EC為前台、IMS為後台

    Returns:
        bool: 如果0筆記錄回傳False , 1筆記錄回傳True
    """
    
    devops_portal_url   = os.getenv("DEVOPS_PORTAL_URL")
    devops_portal_token = os.getenv("DEVOPS_PORTAL_BOT_TOKEN")
    
    
    api_endpoint = f"{devops_portal_url}/devops_portal/api/v1/whitelist"
    headers = {"Authorization": f"Token {devops_portal_token}"}
    params = {"wl_code": f"{wl_id.upper()} {wl_code.upper()}", "fe_type": f"{fe_type.upper()}"}
    resp = requests.get(url=api_endpoint, params=params, headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        if len(data) == 1:
            return True
        elif len(data) == 0:
            return False

def init_whitelist_data(wl_id:str, wl_code:str, ims_allow_ip_list:str, ims_block_ip_list:str, ecp_block_country_list:str):
    """
    初始化白牌黑白名單資料

    Args:
        wl_id (str): 白牌ID
        wl_code (str): 白牌Code
        ims_allow_ip_list (str): 白名單列表(多筆使用分號區隔)
        ims_block_ip_list (str): 黑名單列表(多筆使用分號區隔)
        ecp_block_country_list (str): 地區限制列表(多筆使用分號區隔)
    """

    print(f"進行相關資料初始化")
    print(f"初始化資料: ims_allow_ip_list:{ims_allow_ip_list} , ims_block_ip_list:{ims_block_ip_list}, ecp_block_country_list:{ecp_block_country_list}")
    print("新增Devops-Portal 數據")

    # 初始化Portal該白排的黑白名單數據(前台及後台)
    devops_portal_url   = os.getenv("DEVOPS_PORTAL_URL")
    devops_portal_token = os.getenv("DEVOPS_PORTAL_BOT_TOKEN")
    headers = {"Authorization": f"Token {devops_portal_token}"}
    
    api_endpoint = f"{devops_portal_url}/devops_portal/api/v1/whitelist/"
    ecp_record_exist = check_record_exist(wl_id=wl_id, wl_code=wl_code, fe_type="EC")
    ims_record_exist = check_record_exist(wl_id=wl_id, wl_code=wl_code, fe_type="IMS")

    if ecp_record_exist or ims_record_exist:
        print(f"ecp_record_exist:{ecp_record_exist} ims_record_exist:{ims_record_exist} , 先前初始化似乎沒有完成 , 請先將過去在Devops-Portal建立的資料刪除")
        exit(200)

    # 初始化資料(前台)
    if ecp_record_exist == False:
        payload = {"wl_code": f"{wl_id} {wl_code}", "env": "PROD", "game_type": "MPS", "fe_type": "EC", "whitelist": "", "blacklist": "", "blocked_countries": ecp_block_country_list, "note": "N/A",}
        response = requests.post(url=api_endpoint, json=payload, headers=headers)
        print(response.status_code)
        print(response.json())
        if response.status_code == 201:
            print("前台資料新增完成")

    # 初始化資料(後台)
    if ims_record_exist == False:
        payload = {"wl_code": f"{wl_id} {wl_code}", "env": "PROD", "game_type": "MPS", "fe_type": "IMS", "whitelist": ims_allow_ip_list, "blacklist": ims_block_ip_list, "blocked_countries": "", "note": "N/A",}
        response = requests.post(url=api_endpoint, json=payload, headers=headers)
        print(response.status_code)
        print(response.json())
        if response.status_code == 201:
            print("後台資料新增完成")
    

    # 寫入redis
    print("新增Redis Key")
    update_redis_key(wl_code=wl_code, type="ims_block_ip",      data_list=ims_block_ip_list)
    update_redis_key(wl_code=wl_code, type="ims_allow_ip",      data_list=ims_allow_ip_list)
    update_redis_key(wl_code=wl_code, type="ecp_block_country", data_list=ecp_block_country_list)

def update_redis_key(wl_code:str, type:str, data_list:str):
    """更新黑名單、白名單、地區限制函數

    Args:
        wl_code (str): 白牌Code
        type (str): 
            ims_allow_ip      : 更新後台允許IP的redis key
            ims_block_ip      : 更新後台封鎖IP的redis key
            ecp_block_country : 更新前台地區限制的redis key
        data_list (str): 字串組成的列表, 使用分號分隔列表元素

    """
    
    fet_redis_cluster       = RedisCluster(startup_nodes=fet_redis_cluster_startup_nodes, decode_responses=True)   
    chief_redis_cluster     = RedisCluster(startup_nodes=chief_redis_cluster_startup_nodes, decode_responses=True)   
    azure_z01_redis_cluster = RedisCluster(startup_nodes=azure_z01_redis_cluster_startup_nodes, decode_responses=True)   
    #azure_wjp_redis_cluster = RedisCluster(startup_nodes=azure_wjp_cluster_startup_nodes, decode_responses=True)   
    
    # 該Redis不是使用VM而是雲端整合的redis instance
    azure_redis_cluster     = RedisCluster(startup_nodes=azure_redis_cluster_startup_nodes, decode_responses=True, ssl=True, ssl_cert_reqs=None, password='xerVXMNA7oOoOqg6unlzYVurAmRdnIhbxAzCaHMjFPs=', skip_full_coverage_check=True)
    
    # 判斷更新類型
    if type == "ecp_block_country":
        redis_key = f"MPS-{wl_code.upper()}:::iprule:country"
        redis_val = json.dumps([{"country": f"{country.upper()}"} for country in data_list.split(";")])
        

    elif type == "ims_allow_ip":
        redis_key = f"IMS-{wl_code.upper()}:::iprule:allow"
        redis_val = json.dumps([{"ip": f"{allow_ip_list}"}  for allow_ip_list in data_list.split(';')])
        

    elif type == "ims_block_ip":
        redis_key = f"IMS-{wl_code.upper()}:::iprule:block"
        redis_val = json.dumps([{"ip": f"{block_ip_list}"} for block_ip_list in data_list.split(';')])
            
    # 更新redis & 印出更新結果是否與預期相同
    fet_redis_cluster.set(name=redis_key, value=redis_val)
    print(f"FET: {redis_key} => {fet_redis_cluster.get(name=redis_key)}")

    chief_redis_cluster.set(name=redis_key, value=redis_val)
    print(f"CHIEF: {redis_key} => {chief_redis_cluster.get(name=redis_key)}")

    azure_redis_cluster.set(name=redis_key, value=redis_val)
    print(f"Azure: {redis_key} => {azure_redis_cluster.get(name=redis_key)}")

    azure_z01_redis_cluster.set(name=redis_key, value=redis_val)
    print(f"Azure Redis Cluster for Z01: {redis_key} => {azure_z01_redis_cluster.get(name=redis_key)}")

    #azure_wjp_redis_cluster.set(name=redis_key, value=redis_val)
    #print(f"Azure West Japan: {redis_key} => {azure_wjp_redis_cluster.get(name=redis_key)}")

    print("--------------------------------------------------------------------------------------------------------")
    

def update_devops_portal_data(wl_id:str, wl_code:str, type:str, data_list:str) -> bool:
    """更新黑名單、白名單、地區限制在Devops-Portal的資料

    Args:
        wl_id (str): 白牌ID
        wl_code (str): 白牌Code
        type (str): 
            ims_allow_ip      : 更新後台允許IP的redis key
            ims_block_ip      : 更新後台封鎖IP的redis key
            ecp_block_country : 更新前台地區限制的redis key
        data_list (str): 字串組成的列表, 使用分號分隔列表元素

    """
    
    devops_portal_url   = os.getenv("DEVOPS_PORTAL_URL")
    devops_portal_token = os.getenv("DEVOPS_PORTAL_BOT_TOKEN")
    headers = {"Authorization": f"Token {devops_portal_token}"}
    
    if type == "ecp_block_country":
        payload = {"wl_code": f"{wl_id} {wl_code}", "env": "PROD", "game_type": "MPS", "fe_type": "EC", "blocked_countries": data_list}
        api_endpoint = f"{devops_portal_url}/devops_portal/api/v1/whitelist?wl_code={wl_id.upper()} {wl_code.upper()}&fe_type=EC"

    elif type == "ims_allow_ip":
        payload = {"wl_code": f"{wl_id} {wl_code}", "env": "PROD", "game_type": "MPS", "fe_type": "IMS", "whitelist": data_list}
        api_endpoint = f"{devops_portal_url}/devops_portal/api/v1/whitelist?wl_code={wl_id.upper()} {wl_code.upper()}&fe_type=IMS"

    elif type == "ims_block_ip":
        payload = {"wl_code": f"{wl_id} {wl_code}", "env": "PROD", "game_type": "MPS", "fe_type": "IMS", "blacklist": data_list}
        api_endpoint = f"{devops_portal_url}/devops_portal/api/v1/whitelist?wl_code={wl_id.upper()} {wl_code.upper()}&fe_type=IMS"


    # 查詢該筆紀錄的ID
    response = requests.get(url=api_endpoint, headers=headers)
    data     = response.json()

    if response.status_code == 200:
    
        if len(data) == 1:
            id = response.json()[0]['id']
            api_endpoint = f"{devops_portal_url}/devops_portal/api/v1/whitelist/{id}/"
            response = requests.put(url=api_endpoint, json=payload, headers=headers)
            if response.status_code == 200:
                print(response.json())
                return True
            else:
                print("更新失敗")
                return False

        elif len(data) == 0:
            print("DevopsPortal找不到紀錄, 請確認是否有進行初始化")
            return False

            
        elif len(data) > 1:
            print("DevopsPortal找到超過一筆紀錄, 請確認資訊是否有重複")    
            return False

    elif response.status_code != 200:
        print(f"返回狀態碼: {response.status_code}")
        print(f"訊息: {data}")
        return False



if __name__ == "__main__":
    # 初始化
    # python whitelabel-access-rule.py  X01 INFRATEST a2a3379a6515a762c3b70e07295ffe5ea0d04cd5  --ims_allow_ip_list "1.1.1.1;22.222.13.1" --ims_block_ip_list "0.0.0.0/0" --ecp_block_country_list "TW;PH;CN" --initial
    
    # 更新
    # python whitelabel-access-rule.py  X01 INFRATEST a2a3379a6515a762c3b70e07295ffe5ea0d04cd5  --ims_allow_ip_list "1.1.1.1;22.222.13.1" --ecp_block_country_list "0.0.0.0/0" --ecp_block_country "TW;PH;CN" 

    parser = argparse.ArgumentParser()
    parser.add_argument("wl_id")
    parser.add_argument("wl_code")
    parser.add_argument("--initial", action='store_true')       # action='store_true': 執行命令行時有出現參數則為True , 否則False (用於判斷是否初始化白名單資訊)
    parser.add_argument("--ims_allow_ip_list")
    parser.add_argument("--ims_block_ip_list")
    parser.add_argument("--ecp_block_country_list")
    args = parser.parse_args()

    wl_id                  = args.wl_id
    wl_code                = args.wl_code
    initial                = args.initial
    ims_allow_ip_list      = args.ims_allow_ip_list
    ims_block_ip_list      = args.ims_block_ip_list
    ecp_block_country_list = args.ecp_block_country_list

    # 初始化設置(建站時會使用到)
    if initial == True:
        # 如果沒有指定參數 , 會使用預設內容進行初始化
        if ims_allow_ip_list      == None: ims_allow_ip_list = "1.1.1.1"
        if ims_block_ip_list      == None: ims_block_ip_list = "0.0.0.0/0"
        if ecp_block_country_list == None: ecp_block_country_list = "PH;TW"
        
        init_whitelist_data(wl_id=wl_id, wl_code=wl_code, ims_allow_ip_list=ims_allow_ip_list, ims_block_ip_list=ims_block_ip_list, ecp_block_country_list=ecp_block_country_list)
        print(f"白牌{wl_id} {wl_code}的黑白名單設置初始化完成")

    # 更新黑白名單
    elif initial == False:  
        if ims_allow_ip_list:
            print("準備更新後台IP白名單")
            # 確認Portal資訊儲存成功 , 在更新Redis
            if update_devops_portal_data(wl_id=wl_id, wl_code=wl_code, type="ims_allow_ip", data_list=ims_allow_ip_list) == True:
                update_redis_key(wl_code=wl_code, type="ims_allow_ip", data_list=ims_allow_ip_list)
                print("後台IP白名單更新完成")
            
        if ims_block_ip_list:
            print("準備更新後台IP黑名單")
            # 確認Portal資訊儲存成功 , 在更新Redis
            if update_devops_portal_data(wl_id=wl_id, wl_code=wl_code, type="ims_block_ip", data_list=ims_block_ip_list) == True:
                update_redis_key(wl_code=wl_code, type="ims_block_ip", data_list=ims_block_ip_list)
                print("後台IP黑名單更新完成")

        if ecp_block_country_list:
            print("準備更新前台地區限制")
            # 確認Portal資訊儲存成功 , 在更新Redis
            if update_devops_portal_data(wl_id=wl_id, wl_code=wl_code, type="ecp_block_country", data_list=ecp_block_country_list) == True:
                update_redis_key(wl_code=wl_code, type="ecp_block_country", data_list=ecp_block_country_list)
                print("前台地區限制更新完成")
