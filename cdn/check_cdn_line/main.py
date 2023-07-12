import os
import re
import logging
import requests
import argparse

from dns import resolver, exception
from prettytable import PrettyTable


def init_logging():
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    fh = logging.FileHandler("result.txt")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


def init_prettytable():
    global tb1 

    logging.debug("初始化及設置PrettyTalbe相關屬性")
    tb1 = PrettyTable()
    tb1.field_names = ["domain", "type", "CDN"]
    tb1.align["domain"] = "l"
    tb1.align["type"] = "l"
    tb1.align["CDN"] = "l"


def get_dns_record(domain, fe_type):
    try:
        # DNS初始設定
        dns_resolver = resolver.Resolver()
        dns_resolver.timeout = 3
        dns_resolver.lifetime = 5
        dns_resolver.nameservers = ["1.1.1.1"]
        
        # Response JSON
        result = {"domain": domain,"type": fe_type, "CDN": "N/A"}

        cname=resolver.resolve(domain,'CNAME')

        for answer in cname.response.answer:
            for item in answer.items:
                if 'greycdn' in item.to_text():
                    result.update({"CDN": "GreyPanel"})
                elif 'bzkyman.com' in item.to_text():
                    result.update({"CDN": "Cloudflare Enterprise Plan"})

        return result

    except resolver.NoAnswer as e:
        
        logger.error(e)
        # 如果沒辦法解析出CNAME , 有兩種可能性
        # 1. 可能為 Free Plan 線路 (因為啟用  CF 的 Proxy 所以沒辦法看到CNAME , 而只有實際A紀錄 , 但因A紀錄也不一定是固定的 , 所以用NS做判別 )
        # 2. 可能NS根本就沒有指向過來我方的 Cloudflare Zone
        known_cloudflare_nameserver = [
            "carmelo.ns.cloudflare.com.", 
            "val.ns.cloudflare.com.", 
            "elma.ns.cloudflare.com.", 
            "kevin.ns.cloudflare.com.", 
            "miki.ns.cloudflare.com.", 
            "nick.ns.cloudflare.com.",
            "greg.ns.cloudflare.com.", 
            "tricia.ns.cloudflare.com.",
            "nelly.ns.cloudflare.com.", 
            "tim.ns.cloudflare.com.",
        ]
        regex_pattern = r"^(?P<hostname>www|api|ag|app|bo).(?P<domain_name>.*)$"
        root_domain = re.match(pattern=regex_pattern, string=domain).group("domain_name")
        nameserver = resolver.resolve(root_domain, "NS")
        cf_free_plan_flag = False

        for ns in nameserver.response.answer:
            for item in ns.items:
                if item.to_text() in known_cloudflare_nameserver:
                    cf_free_plan_flag = True
                
        if cf_free_plan_flag == True:
            result.update({"CDN": "Cloudflare Free Plan"})
            return result
        else:
            result.update({"CDN": "Domain's default nameserver not point to Cloudflare"})
            return result
                
    except resolver.NXDOMAIN:
        logger.info("Non-Existent Domain")
        result.update({"CDN": "Domain not exists"})
        
        return result
        
    except exception.Timeout as e:
        logger.info("DNS operation timed out")
        result.update({"CDN": "DNS operation timed out"})
        
        return result
        
    except Exception as e:
        logger.info("其他異常")
        result.update({"CDN": "其他異常"})
        
        return result
        
        
def get_data_from_devops_portal(wl_id:str, wl_code:str, fe_type:str):
    
    DEVOPS_PORTAL_URL = os.getenv("DEVOPS_PORTAL_URL")
    
    api_endpoint = f"{DEVOPS_PORTAL_URL}/devops_portal/api/v1/get_whitelabel_domains"
    params = {
        "env": "prod",
        "fe_type": fe_type,
        "format": "json",
        "game_type": "mps",
        "wl_code": f"{wl_id} {wl_code}"
    }
    domain_list = []
    result = requests.get(url=api_endpoint, params=params)
    result.raise_for_status()
    result = result.json()
    for item in result:
        domain_list.append(item['domain'])
    return domain_list


if __name__ == "__main__":
    # 程式初始化
    init_prettytable()
    init_logging()

    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("wl_id")
    parser.add_argument("wl_code")
    parser.add_argument("fe_type")
    args = parser.parse_args()

    wl_id = args.wl_id.lower()
    wl_code = args.wl_code.lower()
    fe_type = args.fe_type.lower()

    domain_list = get_data_from_devops_portal(wl_id=wl_id, wl_code=wl_code, fe_type=fe_type)

    for domain in domain_list:
        result = get_dns_record(domain=domain, fe_type=fe_type)
        logger.info(result)
        tb1.add_row([result.get("domain"), result.get("type"), result.get("CDN")])

    with open(f"result_{wl_id}_{wl_code}_{fe_type}.txt", "w") as f:
        f.write(tb1.get_string(sortby="CDN"))
    # print(tb1.get_string(sortby="domain"))
