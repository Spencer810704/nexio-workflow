import os
import json
import base64
import logging
import requests
import argparse

from tcppinglib import tcpping
from requests.exceptions import HTTPError
from jinja2 import Environment, FileSystemLoader
from urllib3.exceptions import InsecureRequestWarning

# 設定輸出格式及日誌等級
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s', 
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S',
)

def check_vm_is_up(ip_address:str) -> bool:
    """
    目前尚未查到 Nutanix API 可以檢查 Cloud-init 是否完成
    故先採取檢查SSH 22 Port is open的方式 , 判斷主機已經可以進行Ansible初始化

    Args:
        ip_address (str): IP地址

    Returns:
        bool: 返回主機
    """
    logging.info("ready to check vm is up or not")
    host = tcpping(address=ip_address, port=22, timeout=5, count=10, interval=30)
    return host.is_alive

def generate_cloudinit_user_data(ip_address:str) -> str:
    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("cloud-config.j2")
    data = template.render({"ip_address": ip_address})
    base64_encode_str = base64.b64encode(data.encode("UTF-8")).decode('UTF-8')
    return base64_encode_str

def get_clouinit_payload(user_data:str, hostname:str, wl_code:str) -> dict:
    
    description = json.dumps({"groups": ["mps", "wl", wl_code],"hostvars":{"dc": "fet5f", "env": "prod", "service_type": "mps", "category": "wl", "wl_code": wl_code }})
    
    return  {
        "spec": {
            "name": f"{hostname}",
            "description": description,
            "resources": {
                "power_state": "ON",
                "num_vcpus_per_socket": 4,
                "num_sockets": 1,
                "memory_size_mib": 8192,
                "disk_list": [
                    {
                        "device_properties": {
                            "device_type": "DISK",
                            "disk_address": {
                                "device_index": 0,
                                "adapter_type": "SCSI"
                            }
                        },
                        "data_source_reference": {
                            "kind": "image",
                            "uuid": "12ce3b41-4854-4eb0-b17b-d13a1cb0c4eb"
                        },
                        "disk_size_mib": 30720
                    }
                ],
                "nic_list": [
                    {
                        "nic_type": "NORMAL_NIC",
                        "is_connected": True,
                        "ip_endpoint_list": [
                            {
                                "ip_type": "DHCP"
                            }
                        ],
                        "subnet_reference": {
                            "kind": "subnet",
                            "name": "fet-mps",
                            "uuid": "19e90dec-cd3a-4a3b-8ad2-7326041d173a"
                        }
                    }
                ],
                "guest_tools": {
                    "nutanix_guest_tools": {
                        "state": "ENABLED",
                        "iso_mount_state": "MOUNTED"
                    }
                },
                "guest_customization": {
                    "cloud_init": {
                        "user_data": user_data
                    },
                    "is_overridable": False
                }
            },
            "cluster_reference": {
                "kind": "cluster",
                "name": "NU-FET",
                "uuid": "0005e770-bf45-6f39-3005-7cc25507a43f"
            }
        },
        "api_version": "3.1.0",
        "metadata": {
            "kind": "vm"
        }
    }

def cloud_init(wl_id: str, wl_code:str, vm01_ip_address:str, vm02_ip_address:str):
    try:
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        nutanix_url    = os.getenv("NUTANIX_URL")
        nutanix_user   = os.getenv("NUTANIX_CREDENTIAL_USR")
        nutanix_passwd = os.getenv("NUTANIX_CREDENTIAL_PSW")
        
        create_vm_api_endpoint = f"{nutanix_url}/api/nutanix/v3/vms"
        headers= {"Content-Type": "application/json", "Accept": "application/json"}

        vms = {f"mps01.{wl_code}": vm01_ip_address, f"mps02.{wl_code}": vm02_ip_address}

        # 建立VM
        for hostname, ip_address in vms.items():
            logging.info(f"ready to create vm {hostname}, ip address is {ip_address}...")
            user_data = generate_cloudinit_user_data(ip_address=ip_address)
            payload   = get_clouinit_payload(user_data=user_data, hostname=hostname, wl_code=wl_code)
            logging.info(payload)
            resp = requests.post(url=create_vm_api_endpoint, json=payload, auth=(nutanix_user, nutanix_passwd), headers=headers, verify=False)
            resp.raise_for_status()
            logging.info(f"請求狀態碼: {resp.status_code}")
            
            # 直接跳出異常不繼續建VM , 測試Clone並執行Cloud-init的機器大概2min上下可以完成設定, check_vm_is_up會檢查三分鐘 
            # 如果超過可能就需要檢查其他問題
            if check_vm_is_up(ip_address=ip_address) == False:
                raise Exception("Cloud init virtual machine timed out")
            else:
                logging.info(f"vm {hostname} is up!!")

    except HTTPError as exc:
        code = exc.response.status_code
        logging.info(f"狀態碼:{code} , 請確認異常後重試")
        exit(1)

    except Exception as e:
        # 捕捉異常
        logging.info(e)
        exit(1)

if __name__ == "__main__":

    # 讀取Command參數
    parser = argparse.ArgumentParser()
    parser.add_argument("wl_id")
    parser.add_argument("wl_code")
    parser.add_argument("vm01_ip_address")
    parser.add_argument("vm02_ip_address")
    
    args = parser.parse_args()
    
    wl_id   = args.wl_id.lower()
    wl_code = args.wl_code.lower()
    vm01_ip_address = args.vm01_ip_address
    vm02_ip_address = args.vm02_ip_address

    cloud_init(wl_id=wl_id, wl_code=wl_code, vm01_ip_address=vm01_ip_address, vm02_ip_address=vm02_ip_address)
    

    

    