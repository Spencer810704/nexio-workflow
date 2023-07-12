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


def add_dns_txt_record(record:dict, zone:dict):
    # 讀環境變數
    E_MAIL   = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    AUTH_KEY = os.getenv("CLOUDFLARE_CRENTIALS_PSW")


    hostname                  = record.get('domain', None)
    certificate_verify_key    = record.get('certificate_verify_key', None)
    certificate_verify_value  = record.get('certificate_verify_value', None)
    hostname_pre_verify_key   = record.get('hostname_pre_verify_key', None)
    hostname_pre_verify_value = record.get('hostname_pre_verify_value', None)

    zone_id   = zone.get('zone_id', None)
    zone_name = zone.get('zone_name', None)

    if zone_name == hostname:
        
        api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"

        # Request Header
        headers = {"X-Auth-Key": f"{AUTH_KEY}", "X-Auth-Email": f"{E_MAIL}", "Content-Type": "application/json"}

        # 新增證書驗證TXT 
        body = {"type":"txt", "name":f"{certificate_verify_key}", "content":f"{certificate_verify_value}"}
        response = requests.post(url=api_endpoint, headers=headers, json=body)
        logging.info(response.status_code)

        # 新增自訂主機驗證驗證TXT
        body = {"type":"txt", "name":f"{hostname_pre_verify_key}", "content":f"{hostname_pre_verify_value}"}
        response = requests.post(url=api_endpoint, headers=headers, json=body)
        logging.info(response.status_code)

def get_custom_hostname_validation_record(domain: str) -> dict:

    # 讀環境變數
    ZONE_ID  = os.getenv("CLOUDFLARE_ZONE_ID", None)
    E_MAIL   = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    AUTH_KEY = os.getenv("CLOUDFLARE_CRENTIALS_PSW")


    # Cloudflare API EndPoint
    custom_hostnames_api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/custom_hostnames"
    
    # Request Header
    headers = {"X-Auth-Key": f"{AUTH_KEY}", "X-Auth-Email": f"{E_MAIL}", "Content-Type": "application/json"}
  
    params = {"hostname": domain}

    response_data = requests.get(url=custom_hostnames_api_endpoint, headers=headers, params=params).json()
    result = response_data.get('result', None)    
    
    for item in result:
        # 判斷 pre_validation 狀態 , 如果是被阻擋 , 則直接跳離程式 , 無需後續動作
        pre_validation_status = item.get("status", None)
        if pre_validation_status == "blocked":
            logging.error("this domain was blocked by cloudflare, please choose other domain")
            exit(1)

        # 獲取狀態
        certificate_verify_status = item.get('ssl', None).get('status', None)

        # 篩選狀態是 pending_validation 的 domain
        if certificate_verify_status == 'pending_validation':
            hostname = item.get('hostname', None)
            if hostname == domain:
                txt_verification = certificate_verify_status = item.get('ssl', None).get('validation_records', None)[0]
                ownership_verification = item.get('ownership_verification', None)
                
                return {
                    "domain": hostname,
                    "certificate_verify_key": hostname,
                    "certificate_verify_value": txt_verification.get('txt_value', None),
                    "hostname_pre_verify_key": ownership_verification.get('name', None),
                    "hostname_pre_verify_value": ownership_verification.get('value', None)
                }
        
    
    return None

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
 
def check_certificate_verify_status(domain: str) -> bool:

    # 讀環境變數
    ZONE_ID  = os.getenv("CLOUDFLARE_ZONE_ID", None)
    E_MAIL   = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    AUTH_KEY = os.getenv("CLOUDFLARE_CRENTIALS_PSW")


    # Cloudflare API EndPoint
    custom_hostnames_api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/custom_hostnames"
    
    # Request Header
    headers = {"X-Auth-Key": f"{AUTH_KEY}", "X-Auth-Email": f"{E_MAIL}", "Content-Type": "application/json"}
        
    params = {"hostname": domain}
    response_data = requests.get(url=custom_hostnames_api_endpoint, headers=headers, params=params).json()
    result = response_data.get('result', None)    
    
    for item in result:
        # 獲取狀態
        certificate_verify_status = item.get('ssl', None).get('status', None)

        # 篩選狀態是 pending_validation 的 domain
        if certificate_verify_status == 'active':
            return True
        else:
            return False

def check_pre_validation_status(domain: str) -> bool:

    # 讀環境變數
    ZONE_ID  = os.getenv("CLOUDFLARE_ZONE_ID", None)
    E_MAIL   = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    AUTH_KEY = os.getenv("CLOUDFLARE_CRENTIALS_PSW")


    # Cloudflare API EndPoint
    custom_hostnames_api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/custom_hostnames"
    
    # Request Header
    headers = {"X-Auth-Key": f"{AUTH_KEY}", "X-Auth-Email": f"{E_MAIL}", "Content-Type": "application/json"}
        
    params = {"hostname": domain}
    response_data = requests.get(url=custom_hostnames_api_endpoint, headers=headers, params=params).json()
    result = response_data.get('result', None)    
    
    for item in result:
        # 獲取狀態
        pre_validation_status = item.get('status', None)
        if pre_validation_status == "active":
            return True
        else:
            return False

def switch_root_domain_proxy(zone:dict, domain:str, switch:bool):
    # 讀環境變數
    E_MAIL   = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    AUTH_KEY = os.getenv("CLOUDFLARE_CRENTIALS_PSW")

    zone_id   = zone.get('zone_id', None)
    
    cloudflare_session = requests.Session()
    cloudflare_session.headers.update({"X-Auth-Email": E_MAIL, "X-Auth-Key": AUTH_KEY, "Content-Type": "application/json"})

    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    params = {"type": "cname", "name": domain}
    resp = cloudflare_session.get(url=api_endpoint, params=params)

    if resp.status_code == 200:
        data = resp.json()
        if data['success'] == True:
            result = data['result']
            dns_type = result[0]['type']
            dns_name = result[0]['name']
            dns_record_id = result[0]['id']
            dns_proxy_status = result[0]['proxied']
            dns_record_cname = result[0]['content']
            logging.info(f"dns record id: {dns_record_id}, origin dns proxy status: {dns_proxy_status} and ready to change dns proxy status: {switch}")
            
            update_dns_api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
            resp = cloudflare_session.put(url=update_dns_api_endpoint, json={"type": dns_type, "name": dns_name, "proxied": switch, "content": dns_record_cname})

def add_dns_txt_record(record:dict, zone:dict):
    # 讀環境變數
    E_MAIL   = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    AUTH_KEY = os.getenv("CLOUDFLARE_CRENTIALS_PSW")


    hostname                  = record.get('domain', None)
    certificate_verify_key    = record.get('certificate_verify_key', None)
    certificate_verify_value  = record.get('certificate_verify_value', None)
    hostname_pre_verify_key   = record.get('hostname_pre_verify_key', None)
    hostname_pre_verify_value = record.get('hostname_pre_verify_value', None)

    zone_id   = zone.get('zone_id', None)
    zone_name = zone.get('zone_name', None)

    if zone_name == hostname:
        
        api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"

        # Request Header
        headers = {"X-Auth-Key": f"{AUTH_KEY}", "X-Auth-Email": f"{E_MAIL}", "Content-Type": "application/json"}

        # 新增證書驗證TXT 
        body = {"type":"txt", "name":f"{certificate_verify_key}", "content":f"{certificate_verify_value}"}
        response = requests.post(url=api_endpoint, headers=headers, json=body)
        logging.info(response.status_code)

        # 新增自訂主機驗證驗證TXT
        body = {"type":"txt", "name":f"{hostname_pre_verify_key}", "content":f"{hostname_pre_verify_value}"}
        response = requests.post(url=api_endpoint, headers=headers, json=body)
        logging.info(response.status_code)


if __name__ == "__main__":
    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    args = parser.parse_args()

    # 獲取驗證dns紀錄
    logging.info("ready to get cloudflare enterprise custom hostname validation record")
    custom_hostname_validation_record = get_custom_hostname_validation_record(domain=args.domain)
    logging.info(custom_hostname_validation_record)

    logging.info("ready to get cloudflare zone id by zone name")
    zone_info = get_cloudflare_zone_id(domain=args.domain)
    logging.info(zone_info)

    # 先將二級域名的proxy關閉 , 因為如果開啟的狀況下 , 在驗證時候會不通過
    logging.info("ready to switch root domain proxy off")
    switch_root_domain_proxy(zone=zone_info, domain=args.domain, switch=False)

    # 新增證書驗證及pre
    logging.info("ready to add validation dns record")
    add_dns_txt_record(record=custom_hostname_validation_record, zone=zone_info)

    # 判斷域名有沒有被Cloudflare阻擋 , 有的話後面就不進行動作了 (最開始獲取custom hostname validation record時候有做過一次判斷)
    logging.info("check pre-validation status")
    while(1):
        result = check_pre_validation_status(domain=args.domain)
        if result == True:
            logging.info("custom pre-validation status is active now")
            break
        elif result == False:
            logging.info("waiting for 10 seconds and check it again")
            time.sleep(10)

    logging.info("check certificate verify status")
    while(1):
        result = check_certificate_verify_status(domain=args.domain)
        if result == True:
            logging.info("custom certificate verify status is active now")
            break
        elif result == False:
            logging.info("waiting for 10 seconds and check it again")
            time.sleep(10)

    logging.info("ready to switch root domain proxy on")
    switch_root_domain_proxy(zone=zone_info, domain=args.domain, switch=True)

    logging.info("finish")