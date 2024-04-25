import sys
import os
import requests
import subprocess

# 服务器地址、用户名和密码
BASE_URL = "http://*********:8080"
USERNAME = "***"
PASSWORD = "******"

def get_torrent_info_by_hash(sid, info_hash):
    """
    通过 info hash 获取种子信息
    """
    url = f"{BASE_URL}/api/v2/torrents/info"
    params = {"hashes": info_hash}
    headers = {"Cookie": f"SID={sid}"}
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        torrent_info = response.json()
        if torrent_info:
            file_info = torrent_info[0]
            return file_info.get("name", ""), file_info.get("content_path", ""), file_info.get("tags", ""), file_info.get("save_path", "")
        else:
            print("未找到与 info hash 相关的种子信息")
            return None, None, None, None
    except requests.exceptions.RequestException as e:
        print(f"获取种子信息失败: {e}")
        return None, None, None, None

def process_bdmv_folders(save_path):
    """
    处理 BDMV 文件夹
    """
    for root, dirs, files in os.walk(save_path):
        for d in dirs:
            if d == "BDMV":
                mv_path = os.path.dirname(os.path.join(root, d))
                mv_name = os.path.basename(mv_path)
                iso_file = os.path.join(os.path.dirname(mv_path), f"{mv_name}.iso")
                log_file = f"/home/boxbox/logs/{mv_name}.log"
                
                # 生成 ISO 文件并删除原始目录
                try:
                    subprocess.run(["genisoimage", "-o", iso_file, "-iso-level", "4", "-allow-lowercase", "-l", "-udf", "-allow-limited-size", mv_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    shutil.rmtree(mv_path)
                    print("ISO 文件生成成功并原始目录已删除")
                except subprocess.CalledProcessError as e:
                    print(f"生成 ISO 文件失败: {e}")

def delete_empty_folders(directory):
    """
    删除目录下的空文件夹
    """
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir in dirs:
            full_dir_path = os.path.join(root, dir)
            if not os.listdir(full_dir_path):
                print(f"删除空文件夹: {full_dir_path}")
                os.rmdir(full_dir_path)

def main():
    # 从命令行获取 info hash 参数
    if len(sys.argv) < 2:
        print("未提供 info hash 参数")
        sys.exit(1)
    info_hash_v1 = sys.argv[1]

    # 登录到 qBittorrent
    try:
        login_url = f"{BASE_URL}/api/v2/auth/login"
        data = {"username": USERNAME, "password": PASSWORD}
        response = requests.post(login_url, data=data)
        response.raise_for_status()
        sid = response.cookies.get("SID")
        if sid:
            print("登录成功")
            # 获取种子信息
            name, content_path, tags, save_path = get_torrent_info_by_hash(sid, info_hash_v1)
            if name and save_path:
                # 记录种子信息到日志文件
                with open('/home/boxbox/qbittorrent_script.log', 'a') as log_file:
                    log_file.write(f"种子信息: name={name}, content_path={content_path}, tags={tags}, save_path={save_path}\n")

                # 处理 BDMV 文件夹
                process_bdmv_folders(save_path)
                
                # 处理非 BDMV 文件夹的情况
                if not os.path.exists(os.path.join(save_path, "BDMV")):
                    print("未找到 BDMV 文件夹，执行非原盘操作")
                    command = [
                        "python3",
                        "/home/boxbox/torcp/tp.py",
                        os.path.join(save_path, name),  # 使用 save_path 和 name 结合
                        "-d",
                        f"/home/boxbox/Emby/{name}/",
                        "-s"
                    ]
                    if tags:
                        command.extend(["--imdbid", tags])
                    command.extend([
                        "--tmdb-api-key",
                        "1f749b3a822f0982bf853b1c5c145824",
                        "--origin-name",
                        "--emby-bracket"
                    ])
                    log_command = " ".join(command)
                    print(f"执行命令: {log_command}")
                    with open('/home/boxbox/qbittorrent_script.log', 'a') as log_file:
                        log_file.write(f"执行命令: {log_command}\n")
                    try:
                        with open("/home/boxbox/tp_log.log", "a") as log_file:
                            subprocess.run(command, stdout=log_file, stderr=subprocess.STDOUT, check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"命令执行失败: {e}")

                    # 构建并执行 rclone 命令
                    rclone_command = [
                        "rclone",
                        "move",
                        f"/home/boxbox/Emby/{name}/",
                        "/home/boxbox/MyEmby/",
                        "-v",
                        "--stats",
                        "2000s",
                        "--transfers",
                        "3",
                        "--drive-chunk-size",
                        "32M",
                        "--log-file=/home/boxbox/ttclone.log",
                        "--delete-empty-src-dirs"
                    ]
                    log_rclone_command = " ".join(rclone_command)
                    print(f"执行 rclone 命令：{log_rclone_command}")
                    with open('/home/boxbox/qbittorrent_script.log', 'a') as log_file:
                        log_file.write(f"执行 rclone 命令：{log_rclone_command}\n")
                    try:
                        subprocess.run(rclone_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"rclone 命令执行失败: {e}")
                    
                    # 在执行完rclone命令后删除空文件夹
                    delete_empty_folders("/home/boxbox/Emby")
                    
            else:
                print("未获取到种子信息或者保存路径")
        else:
            print("登录失败")
    except requests.exceptions.RequestException as e:
        print(f"登录到 qBittorrent 失败: {e}")

if __name__ == "__main__":
    main()
