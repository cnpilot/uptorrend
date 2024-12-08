import sys
import os
import requests
import subprocess
import shutil
from threading import Timer

# 服务器地址、用户名和密码
BASE_URL = "http://******:8080"
USERNAME = "***"
PASSWORD = "***"

def get_input_with_timeout(prompt, timeout):
    """
    从命令行获取输入，如果超时则退出程序
    """
    print(prompt)
    timer = Timer(timeout, sys.exit)  # 设置定时器，超时则退出程序
    timer.start()
    try:
        user_input = input()
        timer.cancel()
        return user_input
    except Exception as e:
        timer.cancel()
        print(f"获取输入失败: {e}")
        sys.exit()

def login_qbittorrent():
    """
    登录到 qBittorrent
    """
    try:
        login_url = f"{BASE_URL}/api/v2/auth/login"
        data = {"username": USERNAME, "password": PASSWORD}
        response = requests.post(login_url, data=data)
        response.raise_for_status()
        sid = response.cookies.get("SID")
        if sid:
            print("登录成功")
            return sid
        else:
            print("登录失败")
            return None
    except requests.exceptions.RequestException as e:
        print(f"登录到 qBittorrent 失败: {e}")
        return None

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
    递归处理包含 BDMV 文件夹的目录
    """
    for root, dirs, files in os.walk(save_path):
        for d in dirs:
            if d == "BDMV":
                mv_path = os.path.dirname(os.path.join(root, d))
                mv_name = os.path.basename(mv_path)
                iso_file = os.path.join(os.path.dirname(mv_path), f"{mv_name}.iso")
                log_folder = f"/home/boxbox/logs/{mv_name}"
                log_file_path = os.path.join(log_folder, f"{mv_name}.log")
                
                # 创建日志文件夹
                os.makedirs(log_folder, exist_ok=True)
                
                # 打印正在处理的目录路径
                print(f"处理目录：{mv_path}")
                
                # 生成 ISO 文件并删除原始目录
                try:
                    with open(log_file_path, "a") as log_file:
                        process = subprocess.run(["genisoimage", "-o", iso_file, "-iso-level", "4", "-allow-lowercase", "-l", "-udf", "-allow-limited-size", mv_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                        log_file.write(process.stdout)  # 写入 stdout 到日志文件
                        log_file.write(process.stderr)  # 写入 stderr 到日志文件
                    shutil.rmtree(mv_path)
                    print(f"{mv_name}.iso 文件生成成功并原始目录已删除")
                except subprocess.CalledProcessError as e:
                    print(f"生成 {mv_name}.iso 文件失败: {e}")

def has_bdmv_folder(save_path):
    """
    检查 save_path 及其子文件夹是否含有 BDMV 文件夹
    """
    for root, dirs, files in os.walk(save_path):
        if "BDMV" in dirs:
            return True
    return False

def has_iso_file(save_path):
    """
    检查 save_path 是否包含 ISO 文件
    """
    for root, dirs, files in os.walk(save_path):
        for file in files:
            if file.lower().endswith(".iso"):
                return True
    return False

def is_remux(name):
    """
    判断 name 是否包含 Remux，忽略大小写
    """
    return "remux" in name.lower()

def process_non_bdmv_folders(save_path, name, tags):
    """
    处理非 BDMV 文件夹的逻辑
    """
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
    rclone_destination = "/home/boxbox/MyEmby/Remux/" if is_remux(name) else "/home/boxbox/MyEmby/Encode/"
    rclone_command = [
        "rclone",
        "move",
        f"/home/boxbox/Emby/{name}/",
        rclone_destination,
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
        # 清理空文件夹
        cleanup_command = ["find", "/home/boxbox/Emby", "-type", "d", "-empty", "-exec", "rmdir", "{}", "+"]
        subprocess.run(cleanup_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        print(f"rclone 命令执行失败: {e}")

def main():
    # 从命令行获取种子信息的 info_hash 参数
    if len(sys.argv) < 2:
        info_hash_v1 = get_input_with_timeout("请输入 info hash: ", 60)  # 设置超时时间为60秒
    else:
        info_hash_v1 = sys.argv[1]

    # 登录到 qBittorrent
    sid = login_qbittorrent()
    if sid:
        # 获取种子信息
        name, content_path, tags, save_path = get_torrent_info_by_hash(sid, info_hash_v1)
        if name and save_path:
            # 记录种子信息到日志文件
            with open('/home/boxbox/qbittorrent_script.log', 'a') as log_file:
                log_file.write(f"种子信息: name={name}, content_path={content_path}, tags={tags}, save_path={save_path}\n")

            # 检查是否存在 BDMV 文件夹或 ISO 文件
            if has_bdmv_folder(save_path):
                print("发现 BDMV 文件夹，执行 BDMV 文件夹处理逻辑")
                process_bdmv_folders(save_path)
            elif has_iso_file(save_path):
                print("发现 ISO 文件，跳过处理")
            else:
                print("未发现 BDMV 文件夹或 ISO 文件，执行非 BDMV 文件夹处理逻辑")
                process_non_bdmv_folders(save_path, name, tags)
        else:
            print("未获取到种子信息或者保存路径")
    else:
        print("登录失败")

if __name__ == "__main__":
    main()

