import re
import os
import requests
import argparse

def del_cloudflare_zone(zone_id: str) -> bool:
    
    # get token from environment variable
    cloudflare_account = os.getenv("cloudflare_account")
    cloudflare_token   = os.getenv("cloudflare_token")
    
    cloudflare_session = requests.Session()
    cloudflare_session.headers.update({"X-Auth-Email": cloudflare_account, "X-Auth-Key": cloudflare_token, "Content-Type": "application/json"})

    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
    resp = cloudflare_session.delete(url=api_endpoint)
    if resp.status_code == 200:
        data = resp.json()
        if data['success'] == True:
            result = data['result']
            if len(result) == 1:
                zone_id = result[0]['id']
                print(zone_id)
                return zone_id
            else:
                return None
    else:
        print(f"請求失敗, 狀態碼:{resp.status_code}")
        return None

def del_devops_portal_data(data_id: str) -> bool:
    
    # get token from environment variable
    devops_portal_token = os.getenv("devops_portal_token")
    
    devops_portal_session = requests.Session()
    devops_portal_session.headers.update({"Authorization": f"Token {devops_portal_token}"})
    
    api_endpoint = f"https://devops-portal.admincod88.com/devops_portal/api/v1/whitelabel_info/{data_id}/"
    resp = devops_portal_session.delete(url=api_endpoint)

    if resp.status_code == 200:
        data = resp.json()
        if data['success'] == True:
            result = data['result']
            if len(result) == 1:
                zone_id = result[0]['id']
                print(zone_id)
                return zone_id
            else:
                return None
    else:
        print(f"請求失敗, 狀態碼:{resp.status_code}")
        return None

def get_cloudflare_zone_id(zone_name: str) -> str:
    
    # get token from environment variable
    cloudflare_account = os.getenv("cloudflare_account")
    cloudflare_token   = os.getenv("cloudflare_token")

    cloudflare_session = requests.Session()
    cloudflare_session.headers.update({"X-Auth-Email": cloudflare_account, "X-Auth-Key": cloudflare_token, "Content-Type": "application/json"})

    api_endpoint = f"https://api.cloudflare.com/client/v4/zones?name={zone_name}"
    resp = cloudflare_session.get(url=api_endpoint)
    if resp.status_code == 200:
        data = resp.json()
        if data['success'] == True:
            result = data['result']
            if len(result) == 1:
                zone_id = result[0]['id']
                print(zone_id)
                return zone_id
            else:
                return None
    else:
        print(f"請求失敗, 狀態碼:{resp.status_code}")
        return None

def get_whitelabel_domains_from_portal(wl_code: str) -> dict:
    
    # get token from environment variable
    devops_portal_token = os.getenv("devops_portal_token")
    
    devops_portal_session = requests.Session()
    devops_portal_session.headers.update({"Authorization": f"Token {devops_portal_token}"})

    api_endpoint = f"http://localhost:8080/devops_portal/api/v1/whitelabel_info?wl_code={wl_code}"
    
    resp = devops_portal_session.get(url=api_endpoint)
    
    if resp.status_code == 200:
        datasets = resp.json()
        print(datasets)
        return datasets
    else:
        print(f"請求失敗, 狀態碼:{resp.status_code}")

 
if __name__ == "__main__":
    
    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("wl_id")
    parser.add_argument("wl_code")
    args = parser.parse_args()
    wl_id   = args.wl_id.lower()
    wl_code = args.wl_code.lower()
    
    # 在devops-portal的wl_code格式為: <wl_id>空格<wl_code> , ex: a03 yunhao
    devops_portal_wl_code = f"{wl_id} {wl_code}"
    
    # 取得該白牌下所有使用的域名
    datasets = get_whitelabel_domains_from_portal(wl_code=devops_portal_wl_code)
    for data in datasets:
        # 取得域名 naked domain
        naked_domain = re.match(pattern=r"(?:www\.|bo\.|api\.|ag\.)*([.a-z0-9]+)+", string=data['domain'], flags=re.IGNORECASE).group(1)

        # 取得該筆資料在 Devops-Portal 的 wlinfo 該筆資料的 ID
        data_id = data['id']

        print(f"domain name: {naked_domain}, wl_info data id: {data_id}")

        # # 反查Cloudflare zone id
        # zone_id = get_cloudflare_zone_id(zone_name=naked_domain)
        # if zone_id:
        #     # 刪除Cloudflare Zone , 如果刪除成功則一併刪除Portal上的資料
        #     if del_cloudflare_zone(zone_id=zone_id):
        #         del_devops_portal_data(data_id=data_id)               
        # else:
        #     print(f"在Cloudflare上已找不到該zone: {naked_domain}")