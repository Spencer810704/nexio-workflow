import json
import requests


def generate_post_body(rule_name: str, domain: str, uri: str):
    data = {
        "name": f"{health_check_rule_name}",
        "address": f"{health_ckeck_domain}",
        "type": "HTTPS",
        "http_config": {
            "method": "GET",
            "path": f"{health_ckeck_uri}",
            "port": 443,
            "expected_body": "",
            "expected_codes": ["200"],
            "follow_redirects": False,
            "allow_insecure": False,
            "header": {},
        },
        "tcp_config": None,
        "interval": 10,
        "retries": 2,
        "timeout": 2,
        "check_regions": ["NEAS", "SEAS", "IN"],
        "notification": {"suspended": False, "email_addresses": []},
    }

    return data


if __name__ == "__main__":
    
    # ====================== 修改成要新增的WL_CODE ======================
    wl_code_list = [
        "r50 royalclub"
        # "t18 38",
    ]

    # =================================================================





    # 讀配置
    with open("config/config.json", "r") as file:
        # Load JSON file
        data = json.load(file)

        # 讀取欄位
        E_MAIL = data.get("E_MAIL", None)
        ZONE_ID = data.get("ZONE_ID", None)
        AUTH_KEY = data.get("AUTH_KEY", None)


    for wl_code in wl_code_list:
        print(wl_code)
        wl_id, wl_code = wl_code.split(" ")
        data = requests.get(f"https://devops-portal.admincod88.com/devops_portal/api/v1/get_whitelabel_domains/?env=prod&fe_type=ims&format=json&game_type=mps&wl_code={wl_id}+{wl_code}").json()


        for item in data:

            # 組字串
            health_ckeck_domain = item.get("domain", None).replace("bo", "boapi")
            health_ckeck_uri = f"/{wl_code}-ims/actuator/health"
            health_check_rule_name = f"{wl_id}_{wl_code}-{health_ckeck_domain}"

            # Cloudflare API EndPoint
            health_check_api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/healthchecks"

            # Request Header
            headers = {"X-Auth-Key": f"{AUTH_KEY}", "X-Auth-Email": f"{E_MAIL}", "Content-Type": "application/json"}

            # Request Body
            post_body = generate_post_body(rule_name=health_check_rule_name, domain=health_ckeck_domain, uri=health_ckeck_uri)

            # Send Request
            response = requests.post(url=health_check_api_endpoint, headers=headers, json=post_body)
            print(f"建立 {health_check_rule_name} 規則 , 狀態碼: {response.status_code}")
