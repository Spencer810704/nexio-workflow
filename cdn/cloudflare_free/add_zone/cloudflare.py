import requests

class CloudflareZone():
    
    @property
    def zone_id(self):
        return self._zone_id

    @zone_id.setter
    def zone_id(self, value):
        self._zone_id = value

    @property
    def zone_name(self):
        return self._zone_name 
    
    @zone_name.setter
    def zone_name(self, value):
        self._zone_name = value

    @property
    def name_servers(self):
        return self._name_servers 
    
    @name_servers.setter
    def name_servers(self, value):
        self._name_servers = value

    @property
    def account(self):
        return self._account 
    
    @account.setter
    def account(self, value):
        self._account = value

    def __init__(self, id: str, name: str, account:str, name_servers: list) -> None:
        self._zone_id   = id
        self._zone_name = name
        self._account   = account
        self._name_servers = name_servers

class CloudflareCredential():
    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        self._user = value

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

class CloudflareClient():
    def __init__(self, credential: CloudflareCredential) -> None:
        self._session = requests.Session()
        self._session.headers.update({"X-Auth-Key": f"{credential.token}"})
        self._session.headers.update({"X-Auth-Email": f"{credential.user}"})
        self._session.headers.update({"Content-Type": "application/json"})
        print(self._session.headers)

    def perform_get_request(self, endpoint: str, param: str) -> dict:
        try:
            response_data = self._session.get(url=endpoint, params=param)
            return response_data.json()
        except Exception as e:
            print(e)

    def perform_post_request(self, endpoint: str, payload: dict) -> dict:
        try:
            response_data = self._session.post(url=endpoint, json=payload)
            return response_data.json()
        except Exception as e:
            print(e)

    def perform_patch_request(self, endpoint: str, payload: dict) -> dict:
        try:
            response_data = self._session.patch(url=endpoint, json=payload)
            return response_data.json()
        except Exception as e:
            print(e)

class CloudflareAPI():
    def __init__(self, client: CloudflareClient) -> None:
        self._api_domain = "https://api.cloudflare.com"
        self._client = client

    def list_zone_api(self, domain: str) -> CloudflareZone:
        api_endpoint = f"{self._api_domain}/client/v4/zones"
        params = {"name": domain}
        resp = self._client.perform_get_request(endpoint=api_endpoint, param=params)

        if len(resp['result']) == 1:
            return CloudflareZone(id=resp['result']['id'], name=resp['result']['name'], account=resp['result']['account']['name'],name_servers=resp['result']['name_servers'])
        else:
            return None

    def create_zone_api(self, domain: str) -> CloudflareZone:
        api_endpoint = f"{self._api_domain}/client/v4/zones"
        payload = {"name": domain ,"account": {"id": "4154b0b93bfb4f695b8817fac71b5e97"} }
        resp = self._client.perform_post_request(endpoint=api_endpoint, payload=payload)
        print(resp)
        if resp['success'] == True:
            return CloudflareZone(id=resp['result']['id'], name=resp['result']['name'], account=resp['result']['account']['name'],name_servers=resp['result']['name_servers'])
        else:
            return None  

    def create_dns_record(self, cloudflare_zone: CloudflareZone, record: str, origin_cname: str="prod-mps-bgp-9130.aeorigin.dev", enable_proxy: bool=True) -> bool:
        api_endpoint = f"{self._api_domain}/client/v4/zones/{cloudflare_zone.zone_id}/dns_records"
        payload = {"name": record, "type": "CNAME", "content": origin_cname, "proxied": enable_proxy}
        resp = self._client.perform_post_request(endpoint=api_endpoint, payload=payload)
        return resp['success']

    def create_waf_rules(self, cloudflare_zone: CloudflareZone) -> bool:
        api_endpoint = f"{self._api_domain}/client/v4/zones/{cloudflare_zone.zone_id}/firewall/rules"
        
        payload = [
            # 允許已知Bot
            {"paused": False, "description": "allow_known_bots", "action": "allow","filter": {"expression": "(cf.client.bot)", "paused": False}},
            # 阻擋已知惡意IP列表
            {"paused": False, "description": "blocked_malicious_ip", "action": "block", "filter": {"expression": "(ip.src in $vpn_ip)", "paused": False}},
            # 阻擋國家
            {"paused": True, "description": "block_other_country", "action": "block", "filter": {"expression": "(not ip.geoip.country in {\"VN\" \"TH\" \"IN\" \"PH\" \"MY\" \"HK\" \"ID\" \"US\" \"CN\" \"KH\" \"BD\"})", "paused": False}}
        ]
        resp = self._client.perform_post_request(endpoint=api_endpoint, payload=payload)
        print(resp)
        return resp['success']
    
    def enable_always_https(self, cloudflare_zone: CloudflareZone) -> bool:
        api_endpoint =  f"{self._api_domain}/client/v4/zones/{cloudflare_zone.zone_id}/settings/always_use_https"
        payload = {"value": "on"}
        resp = self._client.perform_patch_request(endpoint=api_endpoint, payload=payload)

        return resp['success']

    def set_https_flexible(self, cloudflare_zone: CloudflareZone) -> bool:
        api_endpoint =  f"{self._api_domain}/client/v4/zones/{cloudflare_zone.zone_id}/settings/ssl"
        payload = {"value": "flexible"}
        resp = self._client.perform_patch_request(endpoint=api_endpoint, payload=payload)
        return resp['success']

    def disable_ipv6(self, cloudflare_zone: CloudflareZone) -> bool:
        api_endpoint =  f"{self._api_domain}/client/v4/zones/{cloudflare_zone.zone_id}/settings/ipv6"
        payload = {"value": "off"}
        resp = self._client.perform_patch_request(endpoint=api_endpoint, payload=payload)
        return resp['success']

    def bypass_service_worker_js(self, cloudflare_zone: CloudflareZone) -> bool:
        # 前台及後台都會配置
        api_endpoint =  f"{self._api_domain}/client/v4/zones/{cloudflare_zone.zone_id}/pagerules"
        payload = {
            "targets": [{
                "target": "url",
                "constraint": {"operator": "matches", "value": f"*.{cloudflare_zone.zone_name}/service-worker.js"}
            }],
            "actions": [{"id": "cache_level", "value": "bypass"}],
            "status": "active"
        }
        resp = self._client.perform_post_request(endpoint=api_endpoint, payload=payload)
        return resp['success']

    def cache_index_html(self, cloudflare_zone: CloudflareZone) -> bool:
        # For EC前台Cache index.html
        api_endpoint =  f"{self._api_domain}/client/v4/zones/{cloudflare_zone.zone_id}/pagerules"
        payload = {
            "targets": [{
                "target": "url",
                "constraint": {
                    "operator": "matches",
                    "value": f"https://www.{cloudflare_zone.zone_name}/index.html"
                }
            }],
            "actions": [{
                "id": "cache_level",
                "value": "cache_everything"
            }],
            "status": "active"
        }
        resp = self._client.perform_post_request(endpoint=api_endpoint, payload=payload)
        return resp['success']
        
    def redirect_www(self, cloudflare_zone: CloudflareZone) -> bool:
        # For EC前台跳轉
        api_endpoint =  f"{self._api_domain}/client/v4/zones/{cloudflare_zone.zone_id}/pagerules"
        payload = {
            "targets": [{
                "target": "url",
                "constraint": {
                    "operator": "matches",
                    "value": f"https://{cloudflare_zone.zone_name}"
                }
            }],
            "actions": [{
                "id": "forwarding_url",
                "value": {
                    "url": f"https://www.{cloudflare_zone.zone_name}",
                    "status_code": 301
                }
            }],
            "priority": 1,
            "status": "active"
        }
        resp = self._client.perform_post_request(endpoint=api_endpoint, payload=payload)
        return resp['success']

