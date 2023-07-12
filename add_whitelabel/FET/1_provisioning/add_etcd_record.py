import os
import json
import etcd3
import argparse
import traceback
import configparser

etcd_host    = os.getenv("ETCD_HOST")
etcd_port    = os.getenv("ETCD_PORT")
etcd_user    = os.getenv("ETCD_CREDENTIAL_USR")
etcd_passwd  = os.getenv("ETCD_CREDENTIAL_PSW")

def change_coredns_record(wl_code, mps01_ip_addr, mps02_ip_addr):
    try:
        # 建立etcd3物件
        etcd_tools = etcd3.client(host=etcd_host, port=etcd_port, user=etcd_user, password=etcd_passwd)

        # 修改mps01 DNS解析
        mps01_key = f"/coredns/tktech/{wl_code}/mps01"
        mps01_value = {"host": mps01_ip_addr, "ttl": 60}
        print(f"修改 {mps01_key} : {mps01_value}")
        etcd_tools.put(key=mps01_key, value=json.dumps(mps01_value))

        # 修改mps02 DNS解析
        mps02_key = f"/coredns/tktech/{wl_code}/mps02"
        mps02_value = {"host": mps02_ip_addr, "ttl": 60}
        print(f"修改 {mps02_key} : {mps02_value}")
        etcd_tools.put(key=mps02_key, value=json.dumps(mps02_value))
        
        # 修改mps vip DNS解析
        mps_vip_key = f"/coredns/tktech/{wl_code}/mps"
        mps_vip_value = {"host": "192.168.27.11", "ttl": 60}
        print(f"修改 {mps_vip_key} : {mps_vip_value}")
        etcd_tools.put(key=mps_vip_key, value=json.dumps(mps_vip_value))

    except Exception as e:
        print(traceback.format_exc())
        exit(1)

def add_mothership_record(wl_code):
    try:
        # 建立etcd3物件
        etcd_tools = etcd3.client(host=etcd_host, port=etcd_port, user=etcd_user, password=etcd_passwd)

        # 新增總後台所需
        etcd_key = f"/whitelabel/prod/mps/{wl_code}"
        etcd_value = f"mps.{wl_code}"
        print(f"修改 {etcd_key} : {etcd_value}")
        etcd_tools.put(key=etcd_key, value=etcd_value)
        
    except Exception as e:
        print(traceback.format_exc())
        exit(1)


if __name__ == "__main__":
    # 範例 :  python modify_dns.py a03 yunhao 
    
    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("wl_id")
    parser.add_argument("wl_code")
    parser.add_argument("mps01_ip_addr")
    parser.add_argument("mps02_ip_addr")
    args = parser.parse_args()

    # 讀取配置檔案
    config = configparser.ConfigParser()
    config.read('config.ini')

    mps01_ip_addr = args.mps01_ip_addr
    mps02_ip_addr = args.mps02_ip_addr
    print(f"mps01 IP: {mps01_ip_addr}")
    print(f"mps02 IP: {mps02_ip_addr}")

    # 修改DNS紀錄
    change_coredns_record(wl_code=args.wl_code, mps01_ip_addr=mps01_ip_addr, mps02_ip_addr=mps02_ip_addr)

    # 新增總後台需要使用的key/value
    add_mothership_record(wl_code=args.wl_code)
    
