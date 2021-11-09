import argparse
import re

import requests
import rsa


class CheckIn:
    login_url = "https://cloud.189.cn/api/portal/loginUrl.action?" \
                "redirectURL=https://cloud.189.cn/web/redirect.html?returnURL=/main.action"
    submit_login_url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
    sign_url = "https://api.cloud.189.cn/mkt/userSign.action?" \
               "clientType=TELEANDROID&version=8.6.3&model=SM-G930K"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = requests.Session()

    def check_in(self):
        self.login()
        url = "https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN"
        url2 = "https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN"
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; SM-G930K Build/NRD90M; wv)"
                          " AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74"
                          ".0.3729.136 Mobile Safari/537.36 Ecloud/8.6.3 Android/22 clie"
                          "ntId/355325117317828 clientModel/SM-G930K imsi/46007111431782"
                          "4 clientChannelId/qq proVersion/1.0.6",
            "Referer": "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
            "Accept-Encoding": "gzip, deflate",
        }
        self.client.headers.update(headers)
        response = self.client.get(self.sign_url)
        net_disk_bonus = response.json()["netdiskBonus"]
        if response.json()["isSign"] == "false":
            print(f"未签到，签到获得{net_disk_bonus}M空间")
        else:
            print(f"已经签到过了，签到获得{net_disk_bonus}M空间")
        response = self.client.get(url, headers=headers)
        if "errorCode" in response.text:
            print(response.text)
        else:
            prize_name = (response.json() or {}).get("prizeName")
            print(f"抽奖获得{prize_name}")
        response = self.client.get(url2, headers=headers)
        if "errorCode" in response.text:
            print(response.text)
        else:
            prize_name = (response.json() or {}).get("prizeName")
            print(f"抽奖获得{prize_name}")

    def login(self):
        r = self.client.get(self.login_url)
        captcha_token = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
        lt = re.findall(r'lt = "(.+?)"', r.text)[0]
        return_url = re.findall(r"returnUrl = '(.+?)'", r.text)[0]
        param_id = re.findall(r'paramId = "(.+?)"', r.text)[0]
        j_rsa_key = re.findall(r'j_rsaKey" value="(\S+)"', r.text, re.M)[0]
        rsa_key_str = f"-----BEGIN PUBLIC KEY-----\n{j_rsa_key}\n-----END PUBLIC KEY-----"
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key_str.encode())

        self.client.headers.update({"lt": lt})
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/76.0",
            "Referer": "https://open.e.189.cn/",
        }
        data = {
            "appKey": "cloud",
            "accountType": "01",
            "userName": f"{{RSA}}{rsa.encrypt(self.username.encode(), pubkey).hex()}",
            "password": f"{{RSA}}{rsa.encrypt(self.password.encode(), pubkey).hex()}",
            "validateCode": "",
            "captchaToken": captcha_token,
            "returnUrl": return_url,
            "mailSuffix": "@189.cn",
            "paramId": param_id,
        }
        r = self.client.post(self.submit_login_url, data=data, headers=headers, timeout=5)
        if r.json()["result"] == 0:
            print(r.json()["msg"])
        else:
            print(r.json()["msg"])
        redirect_url = r.json()["toUrl"]
        self.client.get(redirect_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='天翼云签到脚本')
    parser.add_argument('--username', type=str, help='账号')
    parser.add_argument('--password', type=str, help='密码')
    args = parser.parse_args()
    helper = CheckIn(args.username, args.password)
    helper.check_in()
