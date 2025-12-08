import time
import pywifi
from pywifi import const
from typing import List, TypedDict, Dict

# get_auth_akm_cipher_string 函数保持不变 (可以从上一个回答中复制)
def get_auth_akm_cipher_string(profile):
    """将 pywifi 的常量转换为人类可读的字符串。"""
    auth_map = {
        const.AUTH_ALG_OPEN: "Open", 
        const.AUTH_ALG_SHARED: "Shared Key"
    }
    auth_str = auth_map.get(profile.auth[0], "Unknown")
    
    akm_map = {
        const.AKM_TYPE_WPA: "WPA", 
        const.AKM_TYPE_WPAPSK: "WPA-PSK", 
        const.AKM_TYPE_WPA2: "WPA2", 
        const.AKM_TYPE_WPA2PSK: "WPA2-PSK", 
        const.AKM_TYPE_UNKNOWN: "Unknown"
    }
    akm_str = akm_map.get(profile.akm[0], "Unknown")
    
    cipher_map = {
        const.CIPHER_TYPE_NONE: "None", 
        const.CIPHER_TYPE_WEP: "WEP", 
        const.CIPHER_TYPE_TKIP: "TKIP", 
        const.CIPHER_TYPE_CCMP: "CCMP (AES)", 
        const.CIPHER_TYPE_UNKNOWN: "Unknown"
    }
    cipher_str = cipher_map.get(profile.cipher, "Unknown")
    
    if "PSK" in akm_str:
        auth_str = akm_str
        
    return auth_str, cipher_str


class WiFiNetworkInfo(TypedDict):
    ssid: str
    bssid: str
    signal_strength: int
    auth_type: str
    cipher_type: str


def scan_and_deduplicate_wifi(scan_duration: int) -> List[WiFiNetworkInfo]:
    """
    扫描 Wi-Fi，并对结果进行严格去重，为每个 BSSID 只保留信号最强的记录。
    """
    try:
        wifi = pywifi.PyWiFi()
        iface = wifi.interfaces()[0]
        
        iface.scan()
        time.sleep(scan_duration)  # 等待扫描完成
        
        scan_results = iface.scan_results()

        # 使用字典进行去重，键为 BSSID，值为 profile 对象
        # 这样可以保证每个 BSSID 只出现一次
        unique_bssid_results: Dict[str, pywifi.Profile] = {}
        for profile in scan_results:
            bssid = profile.bssid
            # 如果 BSSID 还没记录，或者当前记录的信号比已记录的要强，则更新
            if (bssid not in unique_bssid_results or 
                profile.signal > unique_bssid_results[bssid].signal):  # type: ignore
                unique_bssid_results[bssid] = profile

        # 将去重后的 profile 对象转换为我们需要的字典格式
        wifi_list: List[WiFiNetworkInfo] = []
        for profile in unique_bssid_results.values():
            ssid = profile.ssid.encode('raw_unicode_escape').decode( # type: ignore
                'utf-8', errors='ignore'
            ).strip()
            if not ssid:
                ssid = "<Hidden Network>"
            
            auth_type, cipher_type = get_auth_akm_cipher_string(profile)
            
            wifi_list.append({
                "ssid": ssid,
                "bssid": profile.bssid,  # type: ignore
                "signal_strength": int(profile.signal),  # type: ignore
                "auth_type": auth_type,
                "cipher_type": cipher_type
            })

        # 按信号强度从强到弱排序
        sorted_wifi_list = sorted(
            wifi_list, 
            key=lambda x: x['signal_strength'], 
            reverse=True
        )
        return sorted_wifi_list

    except IndexError:
        print("错误：未找到无线网络接口。请确保 Wi-Fi 已启用。")
        return []
    except Exception as e:
        print(f"发生未知错误: {e}")
        return []

def connect_to_wifi(ssid, password=None, timeout=10) -> bool:
    """
    连接到指定SSID的WiFi网络
    
    Args:
        ssid (str): 要连接的WiFi网络名称
        password (str, optional): WiFi密码，如果是开放网络则为None
        timeout (int): 连接超时时间（秒）
    
    Returns:
        bool: 连接成功返回True，失败返回False
    """
    wifi = pywifi.PyWiFi()
    
    # 获取第一个无线网卡
    iface = wifi.interfaces()[0]
    
    # 断开当前连接
    iface.disconnect()
    time.sleep(1)
    
    # 创建配置文件
    profile = pywifi.Profile()
    profile.ssid = ssid
    profile.auth = const.AUTH_ALG_OPEN
    
    if password:
        profile.akm.append(const.AKM_TYPE_WPA2PSK)  # WPA2加密
        profile.cipher = const.CIPHER_TYPE_CCMP     # 加密类型
        profile.key = password
    else:
        profile.akm.append(const.AKM_TYPE_NONE)     # 开放网络
        profile.cipher = const.CIPHER_TYPE_NONE
    
    # 移除所有现有配置文件并添加新配置
    iface.remove_all_network_profiles()
    tmp_profile = iface.add_network_profile(profile)
    
    # 尝试连接
    iface.connect(tmp_profile)
    
    # 等待连接结果
    start_time = time.time()
    while time.time() - start_time < timeout:
        if iface.status() == const.IFACE_CONNECTED:
            print(f"成功连接到WiFi: {ssid}")
            return True
        time.sleep(1)
    
    print(f"连接WiFi失败: {ssid}")
    return False


if __name__ == '__main__':
    print(scan_and_deduplicate_wifi(5))