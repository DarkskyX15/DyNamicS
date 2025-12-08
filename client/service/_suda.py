
import re
import sys
import json
import random
import urllib.parse
from base64 import b64decode
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup


def extract_js_code(html_text: str) -> str:
    """
    从HTML文本中提取所有JavaScript代码并返回单个字符串
    
    Args:
        html_text (str): HTML文本
    
    Returns:
        str: 合并后的JavaScript代码字符串
    """
    try:
        # 解析HTML
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # 提取所有script标签中的JavaScript代码
        script_tags = soup.find_all('script')
        js_code = []
        
        for script in script_tags:
            if script.string:  # 只处理内联JS
                js_code.append(script.string.strip())
        
        # 将所有JS代码合并为一个字符串并返回
        return '\n'.join(js_code)

    except Exception:
        # 发生异常时返回空字符串
        return ""

def fetch_and_parse_json(url: str, parse_json: bool = True) -> Any:
    try:
        # 发送GET请求
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        # 获取响应文本并去除两端的小括号
        response_text = response.text.strip()

        # 检查并去除两端的小括号
        if response_text.startswith('(') and response_text.endswith(')'):
            json_text = response_text[1:-1]  # 去除第一个和最后一个字符（小括号）
        else:
            json_text = response_text

        # 如果不解析JSON，直接返回文本
        if not parse_json:
            return json_text

        # 解析JSON
        parsed_json = json.loads(json_text)

        # 格式化并打印JSON
        return parsed_json

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}", file=sys.stderr)
        return None

    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}", file=sys.stderr)
        print(f"原始响应: {response_text}", file=sys.stderr) # type: ignore
        return None

def build_url_with_params(base_url: str, params_dict: Dict[str, Any]) -> str:
    """
    将基础URL和参数字典组合成带请求参数的完整URL

    Args:
        base_url (str): 基础URL
        params_dict (dict): 参数字典

    Returns:
        str: 带请求参数的完整URL
    """
    # 将参数字典编码为查询字符串
    query_string = urllib.parse.urlencode(params_dict)

    # 判断基础URL是否已包含查询参数
    separator = '&' if '?' in base_url else '?'

    # 组合完整URL
    full_url = base_url + separator + query_string

    return full_url

def find_all_matches(text: str, pattern: str) -> List[List[str]]:
    """
    使用正则表达式匹配文本，返回所有匹配的捕获组列表
    
    Args:
        text: 要搜索的文本
        pattern: 正则表达式模式
        
    Returns:
        一个列表的列表，每个内部列表代表一个匹配中的捕获组
        如果没有匹配，返回空列表
    """
    matches = []
    
    # 编译正则表达式
    regex = re.compile(pattern)
    
    # 查找所有匹配
    for match in regex.finditer(text):
        # 获取所有捕获组（从索引1开始，因为索引0是整个匹配）
        groups = list(match.groups())
        matches.append(groups)
    
    return matches


class _Configs:
    base_url: str
    api_url: str
    ip_regex: str
    login_sign: str
    file_ver_regex: str
    isp_url: str
    isp_regex: str
    login_params: dict[str, str]
    add_isp: dict[str, str]
    
    def update(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            data = json.loads(file.read())
        for k, v in data.items():
            setattr(self, k, v)


class SudaLoginClient:

    _config: _Configs
    _index_js: str
    _file_version: str
    _user_ip: str
    _isp_map: dict[str, str]

    _network: bool
    _login: bool
    _have_params: bool

    @property
    def inet_available(self) -> bool:
        return self._network
    @property
    def login_status(self) -> bool:
        return self._login
    @property
    def have_params(self) -> bool:
        return self._have_params
    @property
    def current_ip(self) -> str:
        return self._user_ip

    def __init__(self) -> None:
        self._config = _Configs()
        self._isp_map = {}
        self._have_params = False
        self._network = False
        self._login = False
        self._user_ip = ""


    def update_config(self, path: str = "suda.json") -> None:
        self._config.update(path)

    def update_status(self) -> None:
        self._network = False
        self._login = False
        self._have_params = False

        html = fetch_and_parse_json(self._config.base_url,  False)
        if not html:
            return
        self._network = True

        js_texts = extract_js_code(html)

        if self._config.login_sign in js_texts:
            self._login = True

        file_ver_matches = find_all_matches(js_texts, self._config.file_ver_regex)
        if not file_ver_matches or not file_ver_matches[0]:
            return
        self._file_version = file_ver_matches[0][0]

        user_ips = find_all_matches(js_texts, self._config.ip_regex)
        if not user_ips or not user_ips[0]:
            return
        self._user_ip = user_ips[0][0]
        
        self._have_params = True

    def update_isp(self) -> None:
        if not self.have_params: return

        self._isp_map.clear()
        self._isp_map.update(self._config.add_isp)

        isp_url = self._config.isp_url % self._file_version
        isp_content = fetch_and_parse_json(isp_url, False)
        isp_matches = find_all_matches(isp_content, self._config.isp_regex)
        if not isp_matches:
            return
        for isp in isp_matches:
            self._isp_map[isp[1]] = isp[0]

    def login(self, isp: str, account: str, password: str) -> bool:
        params = {
            "account": account,
            "isp_sign": self._isp_map.get(isp, ""),
            "password": password,
            "user_ip": self._user_ip,
            "rand_num": str(random.randint(1000, 9999))
        }
        post_params = {}
        for key, value in self._config.login_params.items():
            post_params[key] = value.format(**params)
        url = build_url_with_params(self._config.api_url, post_params)
        print("Requesting: %s", url)
        result: dict = fetch_and_parse_json(url, True)
        if not result:
            return False
        if not int(result.get("result", "0")):
            msg = result.get("msg", "")
            if msg:
                msg = b64decode(msg).decode(encoding="utf-8")
            print("Login failed with: %s" % (msg or "unknown", ))
            return False
        self._login = True
        return True


if __name__ == '__main__':
    import time

    client = SudaLoginClient()
    client.update_config()

    while True:
        if not client.login_status:
            client.login("中国移动", "2327405072", "xu711015")
        time.sleep(30)
        client.update_status()

