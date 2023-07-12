import re
import os
import requests
import argparse
from requests.exceptions import HTTPError


def get_waf_rule_id_list(zone_id: str) -> list:
    
    # get token from environment variable
    cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")
    
    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/rules"
    headers = {"X-Auth-Key": f"{cloudflare_token}", "X-Auth-Email": f"{cloudflare_account}", "Content-Type": "application/json"}

    resp = requests.get(url=api_endpoint, headers=headers)
    waf_rules = resp.json()['result']
    return [rule['id'] for rule in waf_rules]
        
def get_waf_filter_id_list(zone_id: str) -> list:

    # get token from environment variable
    cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")

    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/filters"
    headers = {"X-Auth-Key": f"{cloudflare_token}", "X-Auth-Email": f"{cloudflare_account}", "Content-Type": "application/json"}

    resp = requests.get(url=api_endpoint, headers=headers)
    filters = resp.json()['result']
    return [filter['id'] for filter in filters]
        
def del_waf_rules_by_zone(zone_id: str) -> bool:

    try:

        # get token from environment variable
        cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
        cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")

        # 取得這個zone下的 WAF rule id 列表 , 刪除waf rule時需要。
        waf_rule_id_list = get_waf_rule_id_list(zone_id=zone_id)
        
        print("=================== delete waf rules ===================")
        for waf_rule_id in waf_rule_id_list:
            api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/rules/{waf_rule_id}"
            headers = {"X-Auth-Key": f"{cloudflare_token}", "X-Auth-Email": f"{cloudflare_account}", "Content-Type": "application/json"}

            # raise_for_status() 判斷狀態碼非 2xx 時 rasie HTTPError exception
            resp = requests.delete(url=api_endpoint, headers=headers)
            resp.raise_for_status()     

            data = resp.json()
            print(data)
        print("=================== delete waf rules ===================")


        # 當沒有waf rule id 或是全部執行完成後返回True , 以此判別是否有正常完成
        # 如途中發生 timeout、dns解析異常 或是 非2xx狀態碼的狀況時會跳Exception , 最終返回False
        return True

    except HTTPError as exc:
        code = exc.response.status_code
        print(f"狀態碼:{code} , 請確認異常後重試")
        return False

    except Exception as e:
        # 捕捉異常
        print(e)
        return False

def del_waf_filter_object_by_zone(zone_id: str) -> bool:
    try:
        # get token from environment variable
        cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
        cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")
        
        waf_filter_id_list = get_waf_filter_id_list(zone_id=zone_id)

        print("=================== delete waf filter object ===================")

        for filter_id in waf_filter_id_list:
            endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/filters/{filter_id}"
            headers = {"X-Auth-Key": f"{cloudflare_token}", "X-Auth-Email": f"{cloudflare_account}", "Content-Type": "application/json"}
            resp = requests.delete(url=endpoint, headers=headers)
            data = resp.json()
            print(data)

        print("=================== delete waf filter object ===================")

        # 當沒有waf filter id 或是全部執行完成後返回True , 以此判別是否有正常完成
        # 如途中發生 timeout、dns解析異常 或是 非2xx狀態碼的狀況時會跳Exception , 最終返回False
        return True

    except HTTPError as exc:
        code = exc.response.status_code
        print(f"狀態碼:{code} , 請確認異常後重試")
        return False

    except Exception as e:
        # 捕捉異常
        print(e)
        return False

def get_page_rule_id_list(zone_id: str) -> list:
    # get token from environment variable
    cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")
    
    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules"
    headers = {"X-Auth-Key": f"{cloudflare_token}", "X-Auth-Email": f"{cloudflare_account}", "Content-Type": "application/json"}

    resp = requests.get(url=api_endpoint, headers=headers)
    page_rules = resp.json()['result']
    return [rule['id'] for rule in page_rules]
        
def del_page_rules_by_zone(zone_id: str) -> bool:
    
    try:

        # get token from environment variable
        cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
        cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")

        # 取得這個zone下的 WAF rule id 列表 , 刪除 waf rule 時需要。
        page_rule_id_list = get_page_rule_id_list(zone_id=zone_id)
        
        print("=================== delete page rules ===================")

        for page_rule_id in page_rule_id_list:
            api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules/{page_rule_id}"
            headers = {"X-Auth-Key": f"{cloudflare_token}", "X-Auth-Email": f"{cloudflare_account}", "Content-Type": "application/json"}

            # raise_for_status() 判斷狀態碼非 2xx 時 rasie HTTPError exception
            resp = requests.delete(url=api_endpoint, headers=headers)
            resp.raise_for_status()     

            data = resp.json()
            print(data)

        print("=================== delete page rules ===================")

        # 當沒有waf rule id 或是全部執行完成後返回True , 以此判別是否有正常完成
        # 如途中發生 timeout、dns解析異常 或是 非2xx狀態碼的狀況時會跳Exception , 最終返回False
        return True

    except HTTPError as exc:
        code = exc.response.status_code
        print(f"狀態碼:{code} , 請確認異常後重試")
        return False

    except Exception as e:
        # 捕捉異常
        print(e)
        return False

def get_dns_record_id_list(zone_id: str) -> list:
    # get token from environment variable
    cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")
    
    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"X-Auth-Key": f"{cloudflare_token}", "X-Auth-Email": f"{cloudflare_account}", "Content-Type": "application/json"}

    resp = requests.get(url=api_endpoint, headers=headers)
    dns_records = resp.json()['result']
    return [records['id'] for records in dns_records]

def del_dns_record_by_zone(zone_id: str) -> bool:
    
    try:

        # get token from environment variable
        cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
        cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")

        # 取得這個zone下的 WAF rule id 列表 , 刪除 waf rule 時需要。
        dns_record_id_list = get_dns_record_id_list(zone_id=zone_id)
        
        print("=================== delete dns record ===================")

        for dns_record_id in dns_record_id_list:
            api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
            headers = {"X-Auth-Key": f"{cloudflare_token}", "X-Auth-Email": f"{cloudflare_account}", "Content-Type": "application/json"}

            # raise_for_status() 判斷狀態碼非 2xx 時 rasie HTTPError exception
            resp = requests.delete(url=api_endpoint, headers=headers)
            resp.raise_for_status()     

            data = resp.json()
            print(data)

        print("=================== delete dns record ===================")

        # 當沒有waf rule id 或是全部執行完成後返回True , 以此判別是否有正常完成
        # 如途中發生 timeout、dns解析異常 或是 非2xx狀態碼的狀況時會跳Exception , 最終返回False
        return True

    except HTTPError as exc:
        code = exc.response.status_code
        print(f"狀態碼:{code} , 請確認異常後重試")
        return False

    except Exception as e:
        # 捕捉異常
        print(e)
        return False


def del_cloudflare_zone(zone_id: str) -> bool:
    
    try:
        print("=================== delete cloudflare zone ===================")

        # get token from environment variable
        cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
        cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")

        api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
        headers = {"X-Auth-Key": f"{cloudflare_token}", "X-Auth-Email": f"{cloudflare_account}", "Content-Type": "application/json"}
        
        # raise_for_status() 判斷狀態碼非 2xx 時 rasie HTTPError exception
        resp = requests.delete(url=api_endpoint, headers=headers)
        resp.raise_for_status()     

        data = resp.json()
        print(data)

        print("=================== delete cloudflare zone ===================")
        
        return True

    except HTTPError as exc:
        code = exc.response.status_code
        print(f"狀態碼:{code} , 請確認異常後重試")
        return False

    except Exception as e:
        # 捕捉異常
        print(e)
        return False

def del_cf_zone_procedure(zone_id: str):

    # 確認域名下的waf rule完整刪除才執行下一步(如果該域名重複使用時 , 自動化新增規則會因為存在規則引發錯誤)
    if del_waf_rules_by_zone(zone_id=zone_id) == False:
        print("刪除Waf rule發生問題 , 請確認問題後再重新執行")
        exit(1)
    
    # 確認域名下的waf filter物件完整刪除才執行下一步(如果該域名重複使用時 , 自動化新增規則會因為存在規則引發錯誤)
    if del_waf_filter_object_by_zone(zone_id=zone_id) == False:
        print("刪除Waf filter物件發生問題 , 請確認問題後再重新執行")
        exit(1)

    # 確認域名下的page rules完整刪除才執行下一步(如果該域名重複使用時 , 自動化新增規則會因為存在規則引發錯誤)
    if del_page_rules_by_zone(zone_id=zone_id) == False:
        print("刪除Page rule發生問題 , 請確認問題後再重新執行")
        exit(1)

    # DNS紀錄如果在短時間內沒有清除 , CF有可能會暫存紀錄 , 待觀察(如有需要再加入刪除dns record步驟)
    if del_dns_record_by_zone(zone_id=zone_id) == False:
        print("刪除DNS Record發生問題 , 請確認問題後再重新執行")
        exit(1)

    # 最後刪除整個Zone
    if del_cloudflare_zone(zone_id=zone_id) == False:
        print("刪除Zone發生問題 , 請確認問題後再重新執行")
        exit(1)

def get_cloudflare_zone_id(zone_name: str) -> str:
    
    # get token from environment variable
    cloudflare_account = os.getenv("CLOUDFLARE_CRENTIALS_USR")
    cloudflare_token   = os.getenv("CLOUDFLARE_CRENTIALS_PSW")

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
 
if __name__ == "__main__":
    

    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("domain_list", nargs="+")
    args        = parser.parse_args()
    domain_list = args.domain_list
    

    for domain in domain_list:
        # 取得 naked domain
        second_level_domain = re.match(pattern=r"(?:www\.|bo\.|app\.|api\.|ag\.)*([.a-z0-9]+)+", string=domain, flags=re.IGNORECASE).group(1)
        
        # 反查Cloudflare zone id
        zone_id = get_cloudflare_zone_id(zone_name=second_level_domain)

        # 判別zone是否存在 , 若不存在則跳過
        if zone_id:
            print(f"zone name: {second_level_domain}, zone id: {zone_id}")
            del_cf_zone_procedure(zone_id=zone_id)
        else:
            print(f"在Cloudflare上已找不到該zone: {second_level_domain}")