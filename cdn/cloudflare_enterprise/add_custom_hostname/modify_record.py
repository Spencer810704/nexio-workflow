import os
import time
import logging    
import requests
import argparse

from requests.exceptions import HTTPError

# 設定輸出格式及日誌等級
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s', 
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
)




def get_cloudflare_zone_id(domain: str) -> str:
    # 讀環境變數
    E_MAIL   = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    AUTH_KEY = os.getenv("CLOUDFLARE_CRENTIALS_PSW")


    cloudflare_session = requests.Session()
    cloudflare_session.headers.update({"X-Auth-Email": E_MAIL, "X-Auth-Key": AUTH_KEY, "Content-Type": "application/json"})

    api_endpoint = f"https://api.cloudflare.com/client/v4/zones?name={domain}"
    resp = cloudflare_session.get(url=api_endpoint)
    if resp.status_code == 200:
        data = resp.json()
        if data['success'] == True:
            result = data['result']
            if len(result) == 1:
                zone_id = result[0]['id']
                zone_name = result[0]['name']
                return {"zone_id": zone_id, "zone_name": zone_name}
            else:
                return None
    else:
        logging.info(f"請求失敗, 狀態碼:{resp.status_code}")
        return None


def modify_domain_record(zone:dict, domain:str, data_center:str, switch:bool):
    if data_center == "chief":
        custom_origin_server = "cf-mps-bgp-9130.bzkyman.com"

    elif data_center == "azure-ea":
        custom_origin_server = "cf-azure-slb.bzkyman.com"
        
    elif data_center == "fet":
        custom_origin_server = "cf-mps-fet-9029.bzkyman.com"
    # 讀環境變數
    E_MAIL   = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    AUTH_KEY = os.getenv("CLOUDFLARE_CRENTIALS_PSW")

    zone_id   = zone.get('zone_id', None)
    
    cloudflare_session = requests.Session()
    cloudflare_session.headers.update({"X-Auth-Email": E_MAIL, "X-Auth-Key": AUTH_KEY, "Content-Type": "application/json"})

    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    # params = {"type": "cname", "name": domain}
    params = {"type": "cname"}
    try:
        resp = cloudflare_session.get(url=api_endpoint, params=params)
        resp.raise_for_status()
    
    except HTTPError as exc:
        code = exc.response.status_code
        logging.info(f"狀態碼:{code} , 請確認異常後重試")
        exit(1)
    except Exception as e:
    # 捕捉異常
        logging.info(e)
        exit(1)
    
    data = resp.json()
    find_host = ['www', 'api', 'ag', 'bo', 'boapi']

    for record in data['result']:
        if record['name'].split('.')[0] in find_host or record['name'] == domain:
            dns_record_id = record['id']
            update_dns_api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
            resp = cloudflare_session.put(url=update_dns_api_endpoint, json={"type": "CNAME", "name": record['name'], "proxied": True, "content": custom_origin_server})
            logging.info(f"{record['name']} record has already changed to: {custom_origin_server}")
            time.sleep(2)


if __name__ == "__main__":
    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("data_center")
    args = parser.parse_args()


    logging.info("ready to get cloudflare zone id by zone name")
    zone_info = get_cloudflare_zone_id(domain=args.domain)
    logging.info(zone_info)

    logging.info("ready to modify domain record")
    modify_domain_record(zone=zone_info, domain=args.domain, data_center=args.data_center ,switch=True)

    logging.info("finish")