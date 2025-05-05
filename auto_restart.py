import time
import os
import sys
import threading
import subprocess
from datetime import datetime

# 監控與通知參數
HEARTBEAT_INTERVAL = 600  # 10分鐘
FILE_CHECK_INTERVAL = 5   # 5秒
ERROR_RESET_INTERVAL = 300  # 5分鐘
MAX_ERROR_COUNT = 3
ERROR_LOG = 'error.log'

# 你的群組ID與TOKEN（如需自動通知，請自行補充）
GROUP_ID = -1002229824712
API_TOKEN = '8150609743:AAHkPIDjAP_FRiCt-yRBwrh_SY_AqJIjvGQ'

# 心跳、錯誤、檔案監控狀態
error_count = 0
last_error_time = time.time()
last_check_time = time.time()
last_heartbeat = 0

# 如需自動發送通知，請安裝 pyTelegramBotAPI
try:
    import telebot
    bot = telebot.TeleBot(API_TOKEN)
    def send_group_message(msg):
        print(f"[發送群組訊息] {msg}")
        try:
            bot.send_message(GROUP_ID, msg)
        except Exception as e:
            print(f"發送群組訊息失敗: {e}")
except Exception:
    bot = None
    def send_group_message(msg):
        print(f"[通知] {msg}")

# 錯誤日誌
def log_error(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ERROR_LOG, 'a', encoding='utf-8') as f:
        f.write(f'[{now}] {msg}\n')
    print(f'[{now}] {msg}')

# 心跳訊息
def send_heartbeat():
    print("[心跳] 發送心跳訊息")
    try:
        send_group_message('💓 機器人心跳檢測正常運作中')
    except Exception as e:
        log_error(f'心跳訊息發送失敗: {e}')

# 重啟通知
def send_restart_notice(before=True):
    print(f"[重啟通知] before={before}")
    try:
        if before:
            send_group_message('⚠️ 系統即將重新啟動...')
        else:
            send_group_message('✅ 機器人已重新啟動完成')
    except Exception as e:
        log_error(f'重啟通知發送失敗: {e}')

# 心跳監控
def monitor_heartbeat():
    print("[執行緒] 啟動心跳監控")
    global last_heartbeat
    while True:
        now = time.time()
        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            send_heartbeat()
            last_heartbeat = now
        time.sleep(10)

# 錯誤監控
def monitor_errors():
    print("[執行緒] 啟動錯誤監控")
    global error_count, last_error_time
    while True:
        now = time.time()
        if now - last_error_time > ERROR_RESET_INTERVAL:
            error_count = 0
        time.sleep(10)

@bot.message_handler(func=lambda m: m.text and m.text.strip() == '重啟')
def handle_restart(message):
    # 可加權限判斷
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ 此命令僅限管理員使用")
        return
    # 嘗試刪除觸發訊息（避免無限重啟）
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    with open('restart.flag', 'w') as f:
        f.write('restart')
    bot.send_message(message.chat.id, "⚠️ 系統即將重新啟動...")
    import os
    os._exit(0)

# 主程式：守護 bot.py 子進程
def run_bot():
    print("[主程式] 啟動 bot.py 子進程守護")
    global error_count, last_error_time
    while True:
        try:
            print("[主程式] 啟動 bot.py 子進程...")
            proc = subprocess.Popen([sys.executable, 'bot.py'])
            while True:
                # 每1秒檢查一次是否有 restart.flag
                if os.path.exists('restart.flag'):
                    print("[主程式] 偵測到 restart.flag，終止 bot.py 並重啟")
                    proc.terminate()
                    proc.wait()
                    os.remove('restart.flag')
                    break
                if proc.poll() is not None:
                    print("[主程式] bot.py 子進程已結束")
                    break
                time.sleep(1)
        except Exception as e:
            log_error(f'主機器人異常: {e}')
            error_count += 1
            last_error_time = time.time()
            if error_count >= MAX_ERROR_COUNT:
                send_restart_notice(before=True)
                log_error('短時間內錯誤過多，自動重啟')
                error_count = 0
                time.sleep(2)
                continue
        send_restart_notice(before=True)
        time.sleep(2)
        send_restart_notice(before=False)

# 啟動所有監控與主程式
if __name__ == '__main__':
    print("[主程式] 自動重啟監控啟動中...")
    threading.Thread(target=monitor_heartbeat, daemon=True).start()
    threading.Thread(target=monitor_errors, daemon=True).start()
    run_bot()
