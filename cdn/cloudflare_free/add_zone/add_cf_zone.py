import os, sys
import json
import requests
import argparse
from cloudflare import CloudflareAPI, CloudflareClient, CloudflareCredential, CloudflareZone

# Global variable
credential = CloudflareCredential()


def add_dns_record(cloudflare_zone:CloudflareZone, type:str, origin_cname:str="prod-slb-openresty.odano55.com"):
    
    cloudflare_client = CloudflareClient(credential=credential)
    cloudflare_api    = CloudflareAPI(client=cloudflare_client)

    # 判斷要加入的dns record
    if type == "ecp":
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="@", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add root host record success")
        
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="ag", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add ag host record success")
        
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="api", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add api host record success")
        
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="www", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add www host record success")

    elif type == "ims":
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="bo", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add bo host record success")
        
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="boapi", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add boapi host record success")
        
    elif type == "app":
        # 目前雲端或地端都是先指向地端 , 暫時會先Hard Code回源
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="app", origin_cname="prod-dwjt.odano55.com", enable_proxy=True)
        # result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="app", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add app host record success")
    else:
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="@", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add root host record success")
        
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="ag", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add ag host record success")
        
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="api", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add api host record success")
        
        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="www", origin_cname=origin_cname, enable_proxy=True)
        if result: print("Add www host record success")

        result = cloudflare_api.create_dns_record(cloudflare_zone=cloudflare_zone, record="app", origin_cname="prod-dwjt.odano55.com", enable_proxy=True)
        if result: print("Add app host record success")


def add_page_rule(cloudflare_zone:CloudflareZone, type:str):
    
    cloudflare_client = CloudflareClient(credential=credential)
    cloudflare_api    = CloudflareAPI(client=cloudflare_client)

    if type == "ecp":
        result = cloudflare_api.cache_index_html(cloudflare_zone=cloudflare_zone)
        if result == True: print("add cache index.html page rule success")
        result = cloudflare_api.redirect_www(cloudflare_zone=cloudflare_zone)
        if result == True: print("add redirect www page rule success")

    elif type == "ims":
        # 目前後台沒有自訂page rule
        pass
    elif type == "app":
        # 目前APP下載頁沒有自訂page rule
        pass

def init_cf_zone(domain:str) -> CloudflareAPI:
    """
    初始化cloudflare zone(domain) , 此function只配置共用設定(前後台都會使用到的配置)
    - 設定 waf rule
    - 啟用 always https
    - 關閉 ipv6
    - 設定 http flexible
    ( 不做DNS、PageRule配置 , 因需要依照前台或後台去配置不同內容 )

    Args:
        domain (str): 域名

    Returns:
        _type_: _description_
    """

    cloudflare_client = CloudflareClient(credential=credential)
    cloudflare_api = CloudflareAPI(client=cloudflare_client)
    
    # Step 1: 建立Zone
    cloudflare_zone = cloudflare_api.create_zone_api(domain=domain)
    if cloudflare_zone is None:
        cloudflare_zone = cloudflare_api.list_zone_api(domain=domain)
    
    # Step 2: 建立WAF Rule
    if cloudflare_api.create_waf_rules(cloudflare_zone):
        print("create waf success")
    else:
        print("waf rule exists already")
        exit(200)

    # Step 3: 啟用一率HTTPS
    if cloudflare_api.enable_always_https(cloudflare_zone):
        print("enable always https success")
    else:
        print("enable always https failed")
        exit(200)

    # Step 4: 關閉IPV6
    if cloudflare_api.disable_ipv6(cloudflare_zone):
        print("disable ipv6 success")
    else:
        print("disable ipv6 failed")
        exit(200)

    # Step 5: 設定SSL為彈性(443 to 80) , 源站只有使用80port
    if cloudflare_api.set_https_flexible(cloudflare_zone):
        print("set https flexible success")
    else:
        print("set https flexible failed")
        exit(200)

    # Step 6: 設定不快取service_worker.js (不分前後臺)
    if cloudflare_api.bypass_service_worker_js(cloudflare_zone):
        print("set bypass_service_worker_js page rule success")
    else:
        print("set bypass_service_worker_js page rule failed")
        exit(200)

    return cloudflare_zone

def update_devops_portal_info(wl_id:str, wl_code:str, type:str, cloudflare_zone:CloudflareZone):
    token             = os.getenv("DEVOPS_PORTAL_BOT_TOKEN")
    devops_portal_url = os.getenv("DEVOPS_PORTAL_URL")
    
    api_endpoint = f"{devops_portal_url}/api/v1/domain_management/wl_domains/"
    header = {"Authorization": f"Token {token}"}
    
    # payload = {
    #     "wl_code": f"{wl_id.lower()} {wl_code.lower()}",
    #     "env": "prod",
    #     "fe_type": f"{type}",
    #     "game_type": "mps",
    #     "cdn": "CloudFlare",
    #     "note": json.dumps({
    #         "dns": f"Account: {cloudflare_zone.account}", 
    #         "nameserver": cloudflare_zone.name_servers, 
    #         "notes": None
    #     }),
    #     "ag_line": False,
    #     "dwjt_ignore": False,
    #     "ng_group": "MPS",
    #     "status": 0
    # }

    payload = {
        "wl_id": f"{wl_id.lower()}",
        "fe_type_ims": False,
        "fe_type_ecp": False,
        "fe_type_app": False,
        "note": json.dumps({
            "dns": f"Account: {cloudflare_zone.account}", 
            "nameserver": cloudflare_zone.name_servers, 
            "notes": None
        }),
        "status": True
    }
    print(payload)
    print(type)
    print(domain)

    # if type == "ims":
    #     payload.update({"domain": f"bo.{cloudflare_zone.zone_name}"})
    # elif type == "ecp":
    #     # 此處取代ecp成ec的原因是因為舊DevopsPortal使用的名稱是EC , 但實際後端RD溝通使用ECP , 這裡暫時用這種方式處理
    #     payload.update({"fe_type": f"ec"})
    #     payload.update({"domain": f"www.{cloudflare_zone.zone_name}"})
    # elif type == "app":
    #     payload.update({"domain": f"app.{cloudflare_zone.zone_name}"})

    if type == "ims":
        payload.update({"fe_type_ims": True})
        payload.update({"domain": f"{domain}"})
    elif type == "ecp":
        # 此處取代ecp成ec的原因是因為舊DevopsPortal使用的名稱是EC , 但實際後端RD溝通使用ECP , 這裡暫時用這種方式處理
        payload.update({"fe_type_ecp": True})
        # payload.update({"fe_type_app": True})
        payload.update({"domain": f"{domain}"})
    elif type == "app":
        payload.update({"fe_type_app": True})
        # payload.update({"fe_type_ecp": True})
        payload.update({"domain": f"{domain}"})
    else:
        payload.update({"fe_type_app": True})
        payload.update({"fe_type_ecp": True})
        payload.update({"domain": f"{domain}"})


    resp = requests.post(url=api_endpoint, headers=header, json=payload)

    print(resp.status_code)
    print(resp.text)


if __name__ == "__main__":
    # 建立CDN
    
    parser = argparse.ArgumentParser()
    parser.add_argument("wl_id")
    parser.add_argument("wl_code")
    parser.add_argument("--datacenter")
    
    # 配置域名
    parser.add_argument("--domain")
    
    # 配置相關hostname(目前尚未強制規定一條域名只能配一條前台 , 有時候會有一條域名配置前台及APP , 此處需跨部門溝通 , 確定一條域名只能配置一種業務類型)
    parser.add_argument("--ecp", action='store_true') 
    parser.add_argument("--ims", action='store_true') 
    parser.add_argument("--app", action='store_true') 

    args = parser.parse_args()
    wl_id               = args.wl_id
    wl_code             = args.wl_code
    ecp                 = args.ecp
    ims                 = args.ims
    app                 = args.app
    domain              = args.domain
    datacenter          = args.datacenter

    cloudflare_account  = os.getenv("cloudflare_account")
    cloudflare_token    = os.getenv("cloudflare_token")    

    # 初始化
    credential.user  = cloudflare_account
    credential.token = cloudflare_token

    # 建立Zone(前台後台APP共用的部分 , 例如啟用https , waf rules , 關閉ipv6等等)
    cloudflare_zone = init_cf_zone(domain=domain)

    # 判斷要使用哪個機房 ,取得相應CNAME
    origin_cname = {"chief": "prod-mps-bgp-9130.aeorigin.dev", "azure": "prod-slb-openresty.odano55.com", "fet":"prod-mps-fet.aeorigin.dev", "azure-wjp": "prod-azure-wjp-slb.aeorigin.dev"}.get(datacenter.lower())

    # 如果有配置前台 , 新增前台Record、設置跳轉規則


    if ecp == True and app == True:
        add_dns_record(cloudflare_zone, type="both", origin_cname=origin_cname)
        add_page_rule(cloudflare_zone, type="ecp")
        
        # 回寫域名資訊回Devops-Portal
        update_devops_portal_info(wl_id=wl_id, wl_code=wl_code, type="both", cloudflare_zone=cloudflare_zone)
        sys.exit()

    if ecp == True:
        add_dns_record(cloudflare_zone, type="ecp", origin_cname=origin_cname)
        add_page_rule(cloudflare_zone, type="ecp")
        
        # 回寫域名資訊回Devops-Portal
        update_devops_portal_info(wl_id=wl_id, wl_code=wl_code, type="ecp", cloudflare_zone=cloudflare_zone)
    
    # 如果有配置後台 , 只新增Record
    if ims == True:
        add_dns_record(cloudflare_zone, type="ims", origin_cname=origin_cname)
        
        # 回寫域名資訊回Devops-Portal
        update_devops_portal_info(wl_id=wl_id, wl_code=wl_code, type="ims", cloudflare_zone=cloudflare_zone)

    # 如果有配置後台 , 只新增APP Record
    if app == True:
        add_dns_record(cloudflare_zone, type="app", origin_cname=origin_cname)
        
        # 回寫域名資訊回Devops-Portal
        update_devops_portal_info(wl_id=wl_id, wl_code=wl_code, type="app", cloudflare_zone=cloudflare_zone)
