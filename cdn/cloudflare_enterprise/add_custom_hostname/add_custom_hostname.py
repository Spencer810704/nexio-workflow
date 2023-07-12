import os
import time
import logging    
import requests
import argparse
from requests.exceptions import HTTPError

# 設定輸出格式及日誌等級
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s', 
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S',
)


def generate_post_body(domain:str, data_center:str):
    if data_center == "chief":
        custom_origin_server = "cf-mps-bgp-9130.bzkyman.com"

    elif data_center == "azure-ea":
        custom_origin_server = "cf-azure-slb.bzkyman.com"
        
    elif data_center == "fet":
        custom_origin_server = "cf-mps-fet-9029.bzkyman.com"
    
    data = {
        "hostname": f"{domain}",
        "custom_origin_server": custom_origin_server,
        "ssl": {
            "method": "txt",
            "type": "dv",
            "settings": {
                "min_tls_version": "1.0"
            },
            "bundle_method": "ubiquitous",
            "wildcard": True
        }
    }

    return data

def add_custom_hostname(domain:str, data_center:str) -> None:
    try:

        # 讀環境變數
        ZONE_ID  = os.getenv("CLOUDFLARE_ZONE_ID", None)
        E_MAIL   = os.getenv("CLOUDFLARE_CRENTIALS_USR")
        AUTH_KEY = os.getenv("CLOUDFLARE_CRENTIALS_PSW")


        # Cloudflare API EndPoint
        custom_hostname_api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/custom_hostnames"

        # Request Header
        headers = {"X-Auth-Key": f"{AUTH_KEY}", "X-Auth-Email": f"{E_MAIL}", "Content-Type": "application/json"}

        # Request Body
        post_body = generate_post_body(domain=domain, data_center=data_center)
        logging.info(post_body)
        
        # Send Request
        response = requests.post(url=custom_hostname_api_endpoint, headers=headers, json=post_body)
        response.raise_for_status()
        logging.info(f"建立custom hostname: domain , 狀態碼: {response.status_code}")

        time.sleep(5)
        logging.info("waiting 5 seconds for cloudflare enterprise initial..")

    except HTTPError as exc:
        code = exc.response.status_code
        if code == 409:
            logging.info(f"狀態碼:{code} , 請確認物件是否重複")
        else:
            logging.info(f"狀態碼:{code} , 請確認異常後重試")
        exit(1)

    except Exception as e:
        # 捕捉異常
        logging.info(e)
        exit(1)



if __name__ == "__main__":
    

    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("data_center")
    args = parser.parse_args()


    domain      = args.domain
    data_center = args.data_center

    add_custom_hostname(domain=domain, data_center=data_center)