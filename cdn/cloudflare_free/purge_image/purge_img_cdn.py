import os
import logging
import requests
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

def purge_cloudflare_cdn(domain: str, purge_file_list: list):
    CLOUDFLARE_CREDENTIALS_USR = os.getenv("CLOUDFLARE_CREDENTIALS_USR")
    CLOUDFLARE_CREDENTIALS_PSW = os.getenv("CLOUDFLARE_CREDENTIALS_PSW")

    headers = {"X-Auth-Email": CLOUDFLARE_CREDENTIALS_USR, "X-Auth-Key": CLOUDFLARE_CREDENTIALS_PSW}
    zone_id = {"csi.20icipp.com": "53f66ab61c80c13f4b3e5aeaf4a60e70", "img.sitdevops.site": "253de9a01d78154b5055bfd9be1e6d5e", "img.stgdevops.site": "46e1fe96c183902b3a984de0bc13e399", "gic.x8gdkt99.com": "a890cdb0ceb729c25827e1018293eb22"}.get(domain)
    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
    payload      = {"files": [ f"https://{domain}/img/static/{file}" for file in purge_file_list ]}
    logger.info(payload)

    resp = requests.post(url=api_endpoint, headers=headers, json=payload)
    logger.info(resp.text)


def purge_greypanel_cdn(domain: str):
    GREYPANEL_TOKEN = os.getenv("GREYPANEL_TOKEN")
    
    headers = {"greycdn-token": GREYPANEL_TOKEN, "User-Agent": "Greypanel-CDN-API-V3"}
    site_id = {"csi.52ipp.com": 10236, "csi.x8gdkt99.com": 10239}.get(domain)
    params          = {"siteId": site_id}
    api_endpoint = f"https://api.greypanel.com/v3/api/site-cache/purge/site"

    #發送request
    resp   = requests.put(url=api_endpoint, headers=headers, params=params)
    logger.info(resp.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env")
    parser.add_argument("--purge_file_list", nargs="+")
    args = parser.parse_args()
    env  = args.env.lower()
    purge_file_list = args.purge_file_list

    if env == "prod":
        purge_greypanel_cdn(domain="csi.52ipp.com")
        purge_cloudflare_cdn(domain="csi.20icipp.com", purge_file_list=purge_file_list)

    elif env == "uat":
        purge_greypanel_cdn(domain="csi.x8gdkt99.com")
        purge_cloudflare_cdn(domain="gic.x8gdkt99.com", purge_file_list=purge_file_list)
        
    elif env == "stg":
        purge_cloudflare_cdn(domain="img.sitdevops.site", purge_file_list=purge_file_list)

    elif env == "sit":
        purge_cloudflare_cdn(domain="img.sitdevops.site", purge_file_list=purge_file_list)
    
    else:
        exit(200)