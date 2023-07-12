import os
import logging
import requests
import json
import argparse

# 不加名稱設置root logger
logger = logging.getLogger()  

# root logger的預設日誌等級為DEBUG
logger.setLevel(logging.INFO)

# 設置日誌顯示格式以及日期格式
formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s: - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# 使用StreamHandler输出到屏幕
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

# 把Logger掛上這兩個Handler
logger.addHandler(ch)


# 設置 Cloudflare API 資訊
# CLOUDFLARE_CREDENTIALS_USR = os.getenv("CLOUDFLARE_CREDENTIALS_USR")
# CLOUDFLARE_CREDENTIALS_PSW = os.getenv("CLOUDFLARE_CREDENTIALS_PSW")


CLOUDFLARE_CREDENTIALS_USR  = os.getenv("cloudflare_account")
CLOUDFLARE_CREDENTIALS_PSW  = os.getenv("cloudflare_token") 

# 定義函數清除指定域名的緩存
def purge_cache(zone_id, domain):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
    headers = {
        'X-Auth-Email': CLOUDFLARE_CREDENTIALS_USR,
        'X-Auth-Key': CLOUDFLARE_CREDENTIALS_PSW,
        'Content-Type': 'application/json'
    }
    data = {
        'purge_everything': True,
        'hosts': [domain]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print(f"Cache purged for {domain}")
    else:
        print(f"Cache purge failed for {domain}")

# 定義函數根據域名獲取 Cloudflare 上的 ZONE ID
def get_zone_id(domain):
    url = f"https://api.cloudflare.com/client/v4/zones?name={domain}"
    headers = {
        'X-Auth-Email': CLOUDFLARE_CREDENTIALS_USR,
        'X-Auth-Key': CLOUDFLARE_CREDENTIALS_PSW,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data['result']:
            zone_id = data['result'][0]['id']
            return zone_id
    print(f"Failed to get Zone ID for {domain}")




def get_external_domains(wl_id):
    devops_portal_url = os.getenv("DEVOPS_PORTAL_URL") + "/api/v1/domain_management/wl_domains"
    devops_portal_token = os.getenv("DEVOPS_PORTAL_BOT_TOKEN")


    # 創建一個 Session 對象，用於管理 API 的訪問
    session = requests.Session()

    # 使用 Session 對象的 headers 屬性來設置 token
    session.headers.update({'Authorization': f'Token {devops_portal_token}'})
    response = session.get(devops_portal_url)
    logger.info(response.text)

    # 如果請求成功，就把回傳的資料轉換成 JSON 格式並印出來
    if response.status_code == 200:
    #    resources = json.loads(response.content)
    # resources = json.loads(response.content.decode('utf-8'), strict=False)
        resources = json.loads(response.content.decode('utf-8'))
        return(resources[wl_id]['ecp'])
    else:
        print('Error: ' + response.content.decode())

# 測試函數，可以根據需要更改域名
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--wl_id")
    args = parser.parse_args()
    wl_id = args.wl_id.lower()


    domains = get_external_domains(wl_id)
    for d in domains:
        zone_id = get_zone_id(d)
        if zone_id:
            print(zone_id)
            pass
            # purge_cache(zone_id, d)
    # zone_id = get_zone_id(domain)
    # if zone_id:
    #     purge_cache(zone_id, domain)
