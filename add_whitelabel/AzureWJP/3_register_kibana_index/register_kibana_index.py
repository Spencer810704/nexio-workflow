import os
import requests
import argparse


def register_kibana_index(wl_code: str):
    username   = os.getenv("KIBANA_CREDENTIAL_USR")
    password   = os.getenv("KIBANA_CREDENTIAL_PSW")
    kibana_url = os.getenv("KIBANA_URL")

    headers = {'kbn-xsrf': 'anything', 'Content-Type': 'application/json'}
    register_index_endpoint = kibana_url + 'api/data_views/data_view'
    
    print(f"註冊{wl_code}前台index")
    ecp_payload = {'data_view': {'title': f"{wl_code}-ecp-*", 'name': f"{wl_code}-ecp-*", 'timeFieldName': "@timestamp"}}
    resp = requests.post(register_index_endpoint, headers=headers, json=ecp_payload, auth=(username, password))
    print(resp.text)

    if resp.status_code != 200:
        exit(1)

    print(f"註冊{wl_code}後台index")
    ecp_payload = {'data_view': {'title': f"{wl_code}-ims-*", 'name': f"{wl_code}-ims-*", 'timeFieldName': "@timestamp"}}
    resp = requests.post(register_index_endpoint, headers=headers, json=ecp_payload, auth=(username, password))
    print(resp.text)

    if resp.status_code != 200:
        exit(1)

if __name__ == "__main__":
    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("wl_code")
    args = parser.parse_args()
    wl_code = args.wl_code.lower()
    
    # 註冊Kiaban index
    print(f"準備註冊Kiaban index")
    


    register_kibana_index(wl_code=wl_code)