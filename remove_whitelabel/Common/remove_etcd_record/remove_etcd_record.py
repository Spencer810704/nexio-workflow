import os
import sys
import etcd3
import argparse
import traceback

def delete_etcd_record(wl_code):
    try:
        etcd_hsot   = os.getenv("ETCD_HOST")
        etcd_port   = os.getenv("ETCD_PORT")
        etcd_user   = os.getenv("ETCD_CREDENTIALS_USR")
        etcd_passwd = os.getenv("ETCD_CREDENTIALS_PSW")

        # 建立etcd3物件
        etcd_tools = etcd3.client(host=etcd_hsot, port=etcd_port, user=etcd_user, password=etcd_passwd)

        # ======================== 刪除CoreDNS相關紀錄 ========================
        # 刪除 MPS Virtual IP 解析
        mps_vip_key = f"/coredns/tktech/{wl_code}/mps"
        if etcd_tools.delete(key=mps_vip_key):
            print(f"刪除 {mps_vip_key} 成功")
        
        # 刪除 mps01 DNS解析
        mps01_key = f"/coredns/tktech/{wl_code}/mps01"
        if etcd_tools.delete(key=mps01_key):
            print(f"刪除 {mps01_key} 成功")
        
        # 刪除 mps02 DNS解析
        mps02_key = f"/coredns/tktech/{wl_code}/mps02"
        if etcd_tools.delete(key=mps02_key):
            print(f"刪除 {mps02_key} 成功")
        
        # ======================== 刪除總後台相關紀錄 ========================
        mps_mothership_key = f"/whitelabel/prod/mps/{wl_code}"
        if etcd_tools.delete(key=mps_mothership_key):
            print(f"刪除 {mps_mothership_key} 成功")

    except Exception as e:
        print(traceback.format_exc())
        sys.exit(1)



if __name__ == "__main__":
    
    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("--wl_id")
    parser.add_argument("--wl_code")
    args = parser.parse_args()

    # 刪除ETCD紀錄
    print(f"準備刪除 {args.wl_id} {args.wl_code} 的相關紀錄")
    delete_etcd_record(wl_code=args.wl_code)

