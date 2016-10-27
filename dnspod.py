import yaml
import logging
import os
import socket
import requests

def logger():
    LOG_FORMAT = "[%(asctime)s][%(levelname)s] %(message)s"
    LOG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "log")
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG, filename=LOG_FILE)
    return logging.getLogger(__name__)

class LastIP(object):
    def __init__(self):
        self.fn = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lastip")

    def load_ip(self):
        try:
            with open(self.fn, "r") as fp:
                return fp.read()
        except:
            return None

    def save_ip(self, value):
        with open(self.fn, "w") as fp:
            fp.write(value)

class DNSPod(object):
    def __init__(self, login_token):
        self.login_token = login_token
        self.base_url = "https://dnsapi.cn/"
        self.headers = {
            "User-Agent":"haipz.com (haipzm@gmail.com)"
        }

    def get_record_list(self, domain, sub_domain):
        url = self.base_url + "Record.List"
        data = {
            "login_token": self.login_token,
            "format": "json",
            "domain": domain,
            "sub_domain": sub_domain
        }
        try:
            r = requests.post(url, data=data, headers=self.headers)
            if int(r.json()["status"]["code"]) == 1:
                logger().info("Get Record List OK")
                return r.json()["records"]
            else:
                logger().error("Get Record List response: %s", r.text)
                return None
        except Exception, e:
            logger().error("Get Record List Error: %s", e)
            return None

    def update_ddns(self, domain, sub_domain, ip):
        url = self.base_url + "Record.Ddns"
        record_list = self.get_record_list(domain, sub_domain)
        if record_list == None:
            return False
        record = record_list[0]
        record_id = record["id"]
        record_line_id = record["line_id"]
        data = {
            "login_token": self.login_token,
            "format": "json",
            "domain": domain,
            "record_id": record_id,
            "sub_domain": sub_domain,
            "record_line_id": record_line_id,
            "value": ip
        }
        try:
            r = requests.post(url, data=data, headers=self.headers)
            if int(r.json()["status"]["code"]) == 1:
                logger().info("Update DDNS OK")
                return True
            else:
                logger().error("Update DDNS response: %s", r.text)
                return False
        except Exception, e:
            logger().error("Update DDNS Error: %s", e)
            return False

class App(object):
    def __init__(self):
        conf = yaml.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "conf.yaml"), "r"))
        self.login_token = conf["login_token"]
        self.domain = conf["domain"]
        self.sub_domain = conf["sub_domain"]
        self.ip = LastIP().load_ip()

    def run(self):
        ip = self.get_ip()
        dnspod = DNSPod(self.login_token)
        if ip and ip != self.ip:
            logger().info("IP changed from '%s' to '%s'", self.ip, ip)
            if dnspod.update_ddns(self.domain, self.sub_domain, ip):
                self.ip = ip
                LastIP().save_ip(self.ip)

    def get_ip(self):
        try:
            sock = socket.create_connection(address=('ns1.dnspod.net', 6666), timeout=10)
            ip = sock.recv(32)
            sock.close()
            return ip
        except Exception, e:
            logger().error("Get IP Error: %s", e)
            return None

if __name__ == '__main__':
    app = App()
    app.run()