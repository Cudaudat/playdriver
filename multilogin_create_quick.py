import requests, re, os, aiofiles, random
import asyncio, inspect
import pyperclip, json, time
from pathlib import Path



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

def readFile2Arry(iFile):
    with open(iFile, 'r', encoding='utf-8-sig') as file: return [line.strip() for line in file.readlines() if line.strip()]


BEARER = json.load(open(file_bearer, 'r', encoding='utf-8'))['data']['token']
# text = "{'data': {'id': 'cd599f21-cfc9-11ef-985b-0207809f04b9', 'port': '57517'}, 'status': {'error_code': '', 'http_code': 200, 'message': 'Quick profile started successfully'}}"
# match_tmp = re.findall(r"'port':\s*'([^\']+)", str(text), re.I | re.M)
# print(f"{inspect.currentframe().f_lineno} debug +> ", f"{match_tmp[0]}", flush=True)
# exit(f'+++++++++++**********+++++++++++')

# print(f"{inspect.currentframe().f_lineno} debug +> ", f"{BEARER}", flush=True)




async def write_to_file(filename, data, mode="w"):
    """Ghi dữ liệu vào file với khả năng tạo thư mục và file nếu chưa tồn tại.
    Args:
        filename (str): Tên file để ghi dữ liệu.
        data (str hoặc list): Dữ liệu cần ghi. Có thể là một chuỗi hoặc danh sách các dòng.
        mode (str): Chế độ mở file, ví dụ "w", "a". Mặc định là "w" (ghi đè).
    """
    # Tạo thư mục nếu chưa tồn tại
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)  # Tạo thư mục

    # Ghi dữ liệu vào file
    async with aiofiles.open(filename, mode, encoding='utf-8') as file:
        if isinstance(data, list):
            for line in data:
                await file.write(line + "\n")  # Ghi từng dòng trong danh sách và xuống dòng
        else:
            await file.write(str(data) + "\n")  # Ghi dữ liệu đơn và xuống dòng


async def create_multi_profile(proxy_input=None):
    logger.debug(f"create_multi_profile +> {proxy_input}", exc_info=False)
    match_proxy = re.findall(r"[^:@\r\n]+", re.sub("socks5://", "", proxy_input, flags=re.I))
    loop = asyncio.get_event_loop()
    ''' "linux", "macos", "windows", "android" '''

    proxy_set = {
        "type": "socks5",
        "host": f"{match_proxy[2]}",
        "port": int(match_proxy[3]),
        "username": f"{match_proxy[0]}",
        "password": f"{match_proxy[1]}"
    }
    url = "https://launcher.mlx.yt:45001/api/v3/profile/quick"

    payload = {
        "browser_type": "mimic",
        "automation": "playwright",
        "os_type": "windows",
        "is_headless": False,
        "parameters": {
            "fingerprint": {
                "cmd_params": {
                    "params": [
                        {
                            "flag": "blink-settings=imagesEnabled=false",
                            "value": "true"
                        }
                    ]
                }
            },
            "flags": {
                "audio_masking": "mask",
                "fonts_masking": "mask",
                "geolocation_masking": "mask",
                "geolocation_popup": "prompt",
                "graphics_masking": "mask",
                "graphics_noise": "mask",
                "localization_masking": "mask",
                "media_devices_masking": "mask",
                "navigator_masking": "mask",
                "ports_masking": "mask",
                "proxy_masking": "custom",
                "screen_masking": "mask",
                "timezone_masking": "mask",
                "webrtc_masking": "mask"
            },
            "proxy": proxy_set
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {BEARER}"
    }

    response = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, headers=headers))
    logger.warning(f"response +> {response.json()}", exc_info=False)

    if response.status_code ==200:
        match_tmp = re.findall(r'"port":"([^"]+)', str(response.content), re.M)
        # await write_to_file(fileport_multi, f"{match_tmp[0]}", "a")
        logger.info(f"Profile created -> started port-> {match_tmp[0]}", exc_info=False)
    
    if not match_tmp: return create_multi_profile(proxy_input)
    logger.warning(f"debug +> {match_tmp[0]}", exc_info=False)
    pyperclip.copy(match_tmp[0])
    return match_tmp[0]

async def close_browsers():
    loop1 = asyncio.get_event_loop()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': BEARER
    }
    response = await loop1.run_in_executor(None, lambda: requests.get("https://launcher.mlx.yt:45001/api/v1/profile/stop_all?type=quick", headers=headers))
    if response.status_code ==200:
        logger.info(f"Profile stopped ~~ ", exc_info=False)

if __name__ == "__main__":
    asyncio.run(create_multi_profile("socks5://concupx3.custom1:Kocogi233@154.198.34.102:9093"))
    asyncio.run(close_browsers())



# asyncio.run(create_multi_profile("socks5://zzcolqtz7y-zone-moon-region-us:74041908@858067017d3e56f4.tabproxy.vip:5000"))
# asyncio.run(create_multi_profile("socks5://concu_51a.custom10:Kocogi233@154.198.34.58:9093"))
# asyncio.run(close_browsers())
# chrome://settings/content/siteDetails?site=https%3A%2F%2Fwww.academy.com

# chrome://settings/content/images?search=image


# https://www.academy.com/p/new-era-mens-tampa-bay-buccaneers-2024-division-champions-locker-room-cap-?sku=black-one-size-tampa-bay-buccaneers