import json, os, inspect
import requests
import hashlib
import pyperclip
from ctypes import wintypes

from logger import logger
logger.set_console_level("DEBUG")  # This triggers auto call stack tracing!
# 🚀 OPTIMAL CONFIGURATION for AsyncIO + Playwright debugging
logger.configure_call_stack_tracing(
    enabled=False,
    # enabled=True,
    depth=6,
    display_mode='tree',
    show_immediate_caller=False,
    colorize_stack=True,
    show_full_path_no_hidden_for_cross_files=True,
    show_full_path_for_cross_files=True,  # 🚀 Enable full paths!
    path_compression_level="smart",       # 🚀 Smart compression
    different_depth_for_errors=8,
    show_caller_for_warnings=True,
    exclude_modules=[])           # 🚀 Show all modules to see system libraries

BASEDIR, CURRENT_FOLDER, CURRENT_FILE = os.path.dirname(f'{__file__}'), os.path.dirname(f'{__file__}').split('\\')[-1], __file__
file_bearer = fr'{BASEDIR}/bearer.json'

def update_line_from_file(file_path, line_number, new_data):
    """thay đổi dữ liệu của một dòng trong file mà giữ nguyên các dòng khác.
    Parameters:         # line Tính từ 1
    file_path (str): Đường dẫn tới file dữ liệu
    line_number (int): Số thứ tự của dòng cần thay đổi (bắt đầu từ 1)
    new_data: Dữ liệu mới thay thế cho dòng hiện tại
    Returns:    None """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:        # Đọc dữ liệu từ file
            data = file.readlines()
        updated_data = data.copy()      # Tạo bản sao của danh sách dữ liệu để không thay đổi danh sách gốc
        line_index = line_number - 1        # Thay đổi dòng dữ liệu (tính số dòng từ 1)
        if 0 <= line_index < len(data):
            updated_data[line_index] = new_data + '\n'
        else:
            print(f"Số dòng {line_number} không hợp lệ")
        with open(file_path, 'w', encoding='utf-8') as file:        # Lưu lại file sau khi thay đổi
            file.writelines(updated_data)
    except FileNotFoundError:
        print(f"Không tìm thấy file tại đườngdẫn: {file_path}")



MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER = "https://launcher.mlx.yt:45001/api/v2"
LOCAL_HOST = "http://127.0.0.1"
HEADERS = {'Accept': 'application/json',}

#TODO: Insert your account information in both variables below.
USERNAME = "daudat8k8@gmail.com"
PASSWORD = "Caocao23@@"

    # response = requests.post("URL của bạn", data={'key': 'value'})
def sign_in():
    payload = {
        'email': USERNAME,
        'password': hashlib.md5(PASSWORD.encode()).hexdigest()
    }
    # logger.warning(f"payload > {payload}", exc_info=False)
    # exit(f'++++++++++++++++++++++++++++++++++')
    
    r = requests.post(f'{MLX_BASE}/user/signin', json=payload)
    if r.status_code != 200: print(f'\nFailed to login: {r.text}\n')
    else:
        response = json.loads(r.text)
        token = response.get('data').get('token')
        update_line_from_file(file_bearer, 2, token)
        logger.warning(f"info > {response}", exc_info=False)
        with open(file_bearer, 'w', encoding='utf-8') as file:
            file.write(json.dumps(response, ensure_ascii=False))
        # pyperclip.copy(token)
    def set_time_token(token):
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            response = requests.get(f"https://api.multilogin.com/workspace/automation_token?expiration_period=no_exp", headers=headers)
            print(f"{inspect.currentframe().f_lineno} TOKEN Period ==> ", f"{response}", flush=True)
    set_time_token(token)
    return token

# Call the sign_in function to execute it


token = sign_in()
