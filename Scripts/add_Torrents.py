import requests
import re
import time
import json

class QBittorrentClient:
    def __init__(self, qb_config_path, site_config_path):
        self.qb_config = self.load_config(qb_config_path)
        self.site_config = self.load_config(site_config_path)
        self.session = self.login()

    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            return json.load(f)

    def login(self):
        data = {
            'username': self.qb_config['username'],
            'password': self.qb_config['password']
        }
        response = requests.post(f"{self.qb_config['address']}/api/v2/auth/login", data=data)
        response.raise_for_status()
        print("登录成功！")
        return response.cookies

    def add_torrent_from_link(self, torrent_link, save_path, tags=None):
        site_config = self.get_site_config(torrent_link)
        files = {
            'urls': (None, torrent_link),
            'savepath': (None, save_path),
            'category': (None, site_config['name']),  # 设置分类为站点名字
            'skip_checking': (None, 'false'),  # 启用哈希检查
            'paused': (None, 'false')  # 将种子添加为暂停状态
        }
        if tags:
            files['tags'] = (None, tags)  # 将标签设置为IMDb ID
        headers = {'User-Agent': 'Python requests'}
        response = requests.post(f"{self.qb_config['address']}/api/v2/torrents/add", files=files, cookies=self.session, headers=headers)
        response.raise_for_status()
        print(f"种子 {torrent_link} 添加成功！")

    def extract_id_from_url(self, url):
        id_string = url.split('id=')[1].split('&')[0]
        print(f"ID: {id_string}")
        return id_string

    def get_imdb_id_from_url(self, url, cookie):
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
        }
        r = requests.get(url, allow_redirects=True, headers=headers)
        imdb_id = ""
        try:
            imdb_id_match = re.search(r'title/(tt\d+)', r.text)
            if imdb_id_match:
                imdb_id = imdb_id_match.group(1)
                print(f"IMDb ID: {imdb_id}")
        except:
            imdb_id = ""
        return imdb_id

    def process_links(self, links_file):
        with open(links_file, 'r') as file:
            for line in file:
                url = line.strip()
                # Skip empty lines
                if not url:
                    continue
                print(f"处理链接: {url}")
                id_string = self.extract_id_from_url(url)
                site_config = self.get_site_config(url)
                details_url = self.generate_details_url(id_string, site_config['hostname'])
                imdb_id = self.get_imdb_id_from_url(details_url, site_config['cookie'])
                if imdb_id:
                    save_path = f"/home/boxbox/qbittorrent/download/ADE_Bluray_{id_string}_{imdb_id}/"
                    tags = imdb_id  # 使用IMDb ID作为标签
                else:
                    save_path = f"/home/boxbox/qbittorrent/download/{site_config['name']}_{id_string}_no_imdb/"
                    tags = None  # 没有 IMDb ID，不设置标签

                # 根据站点配置的 hostname 决定调用哪个方法来生成下载链接
                if "hdhome.org" in site_config['hostname']:
                    download_url = self.generate_download_url_hdhome(id_string, site_config['cookie'])
                elif "hdsky.me" in site_config['hostname']:
                    download_url = self.generate_download_url_hdsky(id_string, site_config['cookie'])
                else:
                    download_url = self.generate_download_url(id_string, site_config['passkey'], site_config['hostname'])

                print(f"准备添加种子: {download_url}")
                self.add_torrent_from_link(download_url, save_path, tags)
                print("等待 2 秒...")
                time.sleep(3)  # 添加每个种子之间的延迟

    def get_site_config(self, url):
        site_keywords = self.site_config['site_keywords']
        for keyword, config in site_keywords.items():
            if keyword in url:
                return config
        # 如果没有匹配到特定的关键词，则返回默认配置
        return {'name': 'Ubits', 'cookie': 'default_cookie', 'passkey': 'default_passkey', 'hostname': 'ubits.club'}

    def generate_details_url(self, id_string, hostname):
        return f"https://{hostname}/details.php?id={id_string}"

    def generate_download_url(self, id_string, passkey, hostname):
        return f"https://{hostname}/download.php?id={id_string}&passkey={passkey}"

    def generate_download_url_hdhome(self, id_string, cookie):
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
        }
        # 发送HTTP请求获取网页源代码
        url = f"https://hdhome.org/details.php?id={id_string}"
        response = requests.get(url, headers=headers)
        html_content = response.text

        # 使用正则表达式提取种子下载链接
        pattern = r'<a href="(http://hdhome\.org/download\.php\?id=\d+&downhash=[^"]+)">http://hdhome\.org/download\.php\?id=\d+\[.*?\]</a>'
        match = re.search(pattern, html_content)
        
        # 如果找到下载链接，则返回；否则返回空字符串
        if match:
            return match.group(1)
        else:
            return ''

    def generate_download_url_hdsky(self, id_string, cookie):
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
        }
        # 发送HTTP请求获取网页源代码
        url = f"https://hdsky.me/details.php?id={id_string}"
        response = requests.get(url, headers=headers)
        html_content = response.text

        # 使用正则表达式提取种子下载链接
        pattern = r'<a href="(https://hdsky\.me/download\.php\?id=\d+&passkey=[^"]+&sign=[^"]+)">https://hdsky\.me/download\.php\?id=\d+&passkey=\.\.\.</a>'
        match = re.search(pattern, html_content)
        
        # 如果找到下载链接，则返回；否则返回空字符串
        if match:
            return match.group(1)
        else:
            return ''

# 配置文件路径
qb_config_path = '/home/boxbox/qbittorrent_config.json'
site_config_path = '/home/boxbox/site_config.json'

qbittorrent_client = QBittorrentClient(qb_config_path, site_config_path)
qbittorrent_client.process_links('/home/boxbox/links.txt')



