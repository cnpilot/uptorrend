import requests
import re
import time
import json
import os

class QBittorrentClient:
    def __init__(self, qb_config_path, site_config_path):
        self.qb_config = self.load_config(qb_config_path)
        self.site_config = self.load_config(site_config_path)
        self.download_base_path = self.qb_config.get('download_base_path', '/home/boxbox/qbittorrent/download')
        self.metadata_save_path = self.qb_config.get('metadata_save_path', '/home/boxbox/title')
        self.session = self.login()

    def load_config(self, config_path):
        """加载配置文件"""
        with open(config_path, 'r') as f:
            return json.load(f)

    def login(self):
        """登录 qBittorrent 并返回会话"""
        data = {
            'username': self.qb_config['username'],
            'password': self.qb_config['password']
        }
        response = requests.post(f"{self.qb_config['address']}/api/v2/auth/login", data=data)
        response.raise_for_status()
        print("登录成功！")
        return response.cookies

    def ensure_directory_permissions(self, path):
        """确保目录权限正确"""
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            os.chown(path, int(os.getenv("TARGET_UID", 0)), int(os.getenv("TARGET_GID", 0)))
            os.chmod(path, 0o755)
            print(f"目录权限已调整: {path}")

    def calculate_total_size(self):
        """获取所有已添加种子的总大小，并返回 GB 单位的结果"""
        response = requests.get(f"{self.qb_config['address']}/api/v2/torrents/info", cookies=self.session)
        response.raise_for_status()
        torrents = response.json()

        total_size = sum(torrent['size'] for torrent in torrents if 'size' in torrent)
        total_size_gb = total_size / (1024 ** 3)  # 转换为 GB
        print(f"当前种子总大小: {total_size_gb:.2f} GB")
        return total_size_gb  # 返回总大小

    def add_torrent_from_link(self, torrent_link, save_path, tags=None, retries=3):
        """直接通过种子下载链接添加种子到 qBittorrent"""
        files = {
            'urls': (None, torrent_link),
            'savepath': (None, save_path),
            'category': (None, 'default'),
            'skip_checking': (None, 'false'),
            'paused': (None, 'false')
        }
        if tags:
            files['tags'] = (None, tags)
        headers = {'User-Agent': 'Python requests'}
        
        for attempt in range(retries):
            try:
                response = requests.post(f"{self.qb_config['address']}/api/v2/torrents/add", files=files, cookies=self.session, headers=headers)
                response.raise_for_status()
                print(f"种子 {torrent_link} 添加成功！")

                # 计算并打印当前总大小 (GB)
                total_size_gb = self.calculate_total_size()  # 获取总大小 (GB)
                print(f"当前种子总大小: {total_size_gb:.2f} GB")
                return total_size_gb  # 返回总大小

            except requests.RequestException as e:
                print(f"添加种子失败（尝试 {attempt + 1}/{retries}）: {e}")
                if attempt < retries - 1:
                    print("等待2秒后重试...")
                    time.sleep(2)
                else:
                    raise


    def extract_id_from_url(self, url):
        """从链接中提取种子 ID"""
        try:
            id_string = url.split('id=')[1].split('&')[0]
            print(f"ID: {id_string}")
            return id_string
        except IndexError:
            raise ValueError(f"无法从 URL 中提取 ID: {url}")

    def get_imdb_id_and_titles_from_url(self, url, cookie):
        """从种子详情页提取 IMDb ID 和标题、副标题"""
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
        }
        try:
            r = requests.get(url, allow_redirects=True, headers=headers)
            html = r.text

            imdb_id = "未找到 IMDb ID"
            title = "未找到标题"
            subtitle = "未找到副标题"

            # 提取 IMDb ID
            imdb_id_match = re.search(r'title/(tt\d+)', html)
            if imdb_id_match:
                imdb_id = imdb_id_match.group(1)

            # 提取标题并格式化
            title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
            if title_match:
                raw_title = title_match.group(1).strip()
                formatted_title = re.sub(r' - Powered by NexusPHP$', '', raw_title)
                formatted_title = formatted_title.replace('&quot;', '"')
                formatted_title = formatted_title.replace('种子详情', '种子详情 ::', 1)  # 替换一次即可
                title = formatted_title.strip()

            # 提取副标题
            subtitle_match = re.search(
                r'<td class="rowhead nowrap".*?>副标题</td>\s*<td class="rowfollow".*?>(.*?)</td>',
                html,
                re.DOTALL,
            )
            if subtitle_match:
                subtitle = subtitle_match.group(1).strip()

            print(f"IMDb ID: {imdb_id}, 标题: {title}, 副标题: {subtitle}")
            return imdb_id, title, subtitle

        except Exception as e:
            print(f"解析详情页出错: {e}")
            return "未找到 IMDb ID", "未找到标题", "未找到副标题"

    def save_details_to_file(self, id_string, site_name, title, subtitle, imdb_id, file_type="regular"):
        """保存详情到文本文件"""
        save_path = self.metadata_save_path if file_type == "regular" else '/home/boxbox/Subtitle'
        self.ensure_directory_permissions(save_path)
        file_path = os.path.join(save_path, f"{site_name}_{id_string}.txt")

        with open(file_path, 'w') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Subtitle: {subtitle}\n")
            f.write(f"IMDb ID: {imdb_id}\n")
        print(f"详情保存到: {file_path}")

    def save_details_to_cleaned_file(self, id_string, site_name, title, subtitle, imdb_id, qb_save_path=None):
        """保存种子详情到清理后的文本文件，文件名为 {site_name}_{id_string}_{imdb_id}_{cleaned_subtitle}.txt"""

        # 替换未找到的 IMDb ID 为 "No_IMDb"
        if imdb_id == "未找到 IMDb ID":
            imdb_id = "No_IMDb"

        # 清理副标题
        cleaned_subtitle = subtitle.strip()
        cleaned_subtitle = re.sub(r'[<>:"/\\|?*]', '', cleaned_subtitle)  # 移除非法字符
        cleaned_subtitle = re.sub(r'\s+', ' ', cleaned_subtitle)  # 合并多余空格
        cleaned_subtitle = cleaned_subtitle.replace(' ', '_')  # 将空格替换为下划线

        # 设置副标题最大长度为 90
        max_subtitle_length = 70

        # 计算文件名的总长度，扣除路径部分
        save_path = '/home/boxbox/Subtitle'
        path_length = len(save_path) + 1  # 包含文件夹路径和分隔符的长度
        max_filename_length = 255 - path_length  # 255 是文件路径的最大限制

        # 计算副标题最大可用长度，考虑到其他部分（site_name, id_string, imdb_id）的长度
        max_available_subtitle_length = max_filename_length - len(site_name) - len(id_string) - len(imdb_id) - 3  # 3 是下划线的长度

        # 只裁剪副标题部分，不影响其他部分
        cleaned_subtitle = cleaned_subtitle[:min(max_available_subtitle_length, max_subtitle_length)]

        # 构造文件名
        file_name = f"{site_name}_{id_string}_{imdb_id}_{cleaned_subtitle}.txt"

        # 确保最终文件名不超过最大限制
        if len(file_name) > 255:
            print(f"文件名过长，已裁剪为: {file_name[:255]}")
            file_name = file_name[:255]

        file_path = os.path.join(save_path, file_name)

        # 保存文件
        with open(file_path, 'w') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Subtitle: {subtitle}\n")
            f.write(f"IMDb ID: {imdb_id}\n")

        print(f"详情已保存到: {file_path}")

        if qb_save_path:
            self.ensure_directory_permissions(qb_save_path)
            qb_file_path = os.path.join(qb_save_path, file_name)

            # 确保 qb 保存路径也不会超过 255 个字符
            if len(qb_file_path) > 255:
                print(f"qb 文件路径过长，已裁剪为: {qb_file_path[:255]}")
                qb_file_path = qb_file_path[:255]

            # 保存到 qBittorrent 路径
            with open(qb_file_path, 'w') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Subtitle: {subtitle}\n")
                f.write(f"IMDb ID: {imdb_id}\n")

            print(f"详情已保存到 qBittorrent 路径: {qb_file_path}")

    def get_site_config(self, url):
        """根据链接匹配站点配置"""
        site_keywords = self.site_config['site_keywords']
        for keyword, config in site_keywords.items():
            if keyword in url:
                return config
        print(f"警告: 未找到匹配站点配置，使用默认配置: {url}")
        return {'name': 'Ubits', 'cookie': 'default_cookie', 'passkey': 'default_passkey', 'hostname': 'ubits.club'}

    def generate_details_url(self, id_string, hostname):
        """生成种子详情页 URL"""
        return f"https://{hostname}/details.php?id={id_string}"

    def generate_download_url(self, id_string, passkey, hostname):
        """生成种子下载 URL"""
        return f"https://{hostname}/download.php?id={id_string}&passkey={passkey}"
        
    def generate_download_url_hdhome(self, id_string, cookie):
        """生成 HDHome 种子下载链接"""
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
        }
        url = f"https://hdhome.org/details.php?id={id_string}"
        response = requests.get(url, headers=headers)
        html_content = response.text
        pattern = r'<a href="(http://hdhome\.org/download\.php\?id=\d+&downhash=[^"]+)">'
        match = re.search(pattern, html_content)
        return match.group(1) if match else ''

    def generate_download_url_hdsky(self, id_string, cookie):
        """生成 HDSky 种子下载链接"""
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
        }
        url = f"https://hdsky.me/details.php?id={id_string}"
        response = requests.get(url, headers=headers)
        html_content = response.text
        pattern = r'<a href="(https://hdsky\.me/download\.php\?id=\d+&passkey=[^"]+&sign=[^"]+)">'
        match = re.search(pattern, html_content)
        return match.group(1) if match else ''

    def process_links(self, links_file):
        """处理链接文件并逐个通过种子下载链接添加种子到 qBittorrent"""

        with open(links_file, 'r') as file:
            for line in file:
                url = line.strip()
                if not url:
                    continue
                try:
                    print(f"处理链接: {url}")
                    id_string = self.extract_id_from_url(url)
                    site_config = self.get_site_config(url)
                    details_url = f"https://{site_config['hostname']}/details.php?id={id_string}"
                    imdb_id, title, subtitle = self.get_imdb_id_and_titles_from_url(details_url, site_config['cookie'])

                    # 如果 IMDb ID 未找到，将其设置为 "No_IMDb"
                    if imdb_id == "未找到 IMDb ID":
                        imdb_id = "No_IMDb"

                    # 保存详情信息到常规文件
                    self.save_details_to_file(id_string, site_config['name'], title, subtitle, imdb_id)

                    # 保存详情信息到清理后的文件，并同时保存到 qBittorrent 路径
                    save_path = os.path.join(self.download_base_path, f"{site_config['name']}_{id_string}_{imdb_id}/")
                    self.save_details_to_cleaned_file(id_string, site_config['name'], title, subtitle, imdb_id, save_path)

                    tags = imdb_id if imdb_id != "No_IMDb" else None

                    # 生成种子下载链接
                    if "hdhome.org" in site_config['hostname']:
                        download_url = self.generate_download_url_hdhome(id_string, site_config['cookie'])
                    elif "hdsky.me" in site_config['hostname']:
                        download_url = self.generate_download_url_hdsky(id_string, site_config['cookie'])
                    else:
                        download_url = f"https://{site_config['hostname']}/download.php?id={id_string}&passkey={site_config['passkey']}"

                    # 直接添加种子下载链接
                    self.add_torrent_from_link(download_url, save_path, tags)
                    
                    print("等待 2 秒...")
                    time.sleep(2)
                except Exception as e:
                    print(f"处理链接时出错: {e}")


if __name__ == "__main__":
    qb_config_path = '/home/boxbox/qbittorrent_config.json'
    site_config_path = '/home/boxbox/site_config.json'

    os.environ["TARGET_UID"] = str(os.stat('/home/boxbox').st_uid)
    os.environ["TARGET_GID"] = str(os.stat('/home/boxbox').st_gid)

    qbittorrent_client = QBittorrentClient(qb_config_path, site_config_path)
    qbittorrent_client.process_links('/home/boxbox/links.txt')


