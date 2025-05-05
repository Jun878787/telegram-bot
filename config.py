import json
import os
from datetime import datetime

class Config:
    def __init__(self):
        self.config_file = 'config.json'
        self.data = {
            'deposits': [],
            'withdrawals': [],
            'operators': [],
            'rates': {
                'deposit': 33.25,
                'withdrawal': 33.25
            },
            'broadcast_mode': False,
            'welcome_message': '👋 歡迎 {SURNAME} Go to 北金 North™Sea ᴍ8ᴘ👋',
            'farewell_enabled': True,
            'farewell_message': '👋 {SURNAME} 已離開群組，期待再相會！'
        }
        self.load_data()

    def load_data(self):
        """載入配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                self.data.update(loaded_data)
        self.save_data()

    def save_data(self):
        """保存配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_transaction(self, amount, type_, currency=None, username=None, user_id=None, date=None):
        """添加交易記錄，支援幣別、成員資訊與日期"""
        transaction = {
            'time': datetime.now().strftime('%H:%M'),
            'amount': amount if type_ == 'deposit' else -abs(amount),
            'currency': currency if currency else 'TWD',
            'username': username,
            'user_id': user_id,
            'date': date
        }
        if type_ == 'deposit':
            self.data['deposits'].append(transaction)
        else:
            self.data['withdrawals'].append(transaction)
        self.save_data()
        return True

    def cancel_last_deposit(self):
        """撤銷最後一筆入款"""
        if self.data['deposits']:
            self.data['deposits'].pop()
            self.save_data()
            return True
        return False

    def cancel_last_withdrawal(self):
        """撤銷最後一筆出款"""
        if self.data['withdrawals']:
            self.data['withdrawals'].pop()
            self.save_data()
            return True
        return False

    def get_transaction_summary(self):
        """獲取交易摘要，支援多幣別"""
        total_deposit = sum(t['amount'] for t in self.data['deposits'])
        processed_amount = sum(t['amount'] for t in self.data['withdrawals'])
        return {
            'deposits': self.data['deposits'],
            'withdrawals': self.data['withdrawals'],
            'deposit_count': len(self.data['deposits']),
            'withdrawal_count': len(self.data['withdrawals']),
            'total_deposit': total_deposit,
            'processed_amount': abs(processed_amount)
        }

    def get_rates(self):
        """獲取匯率"""
        return self.data['rates']

    def set_deposit_rate(self, rate):
        """設定入款匯率"""
        self.data['rates']['deposit'] = float(rate)
        self.save_data()

    def set_withdrawal_rate(self, rate):
        """設定出款匯率"""
        self.data['rates']['withdrawal'] = float(rate)
        self.save_data()

    def set_broadcast_mode(self, enabled):
        """設定群發廣播模式"""
        self.data['broadcast_mode'] = enabled
        self.save_data()

    def is_broadcast_mode(self):
        """檢查是否為群發廣播模式"""
        return self.data.get('broadcast_mode', False)

    def is_operator(self, user_id):
        """檢查用戶是否為操作員"""
        return str(user_id) in self.data['operators']

    def add_operator(self, user_id):
        """添加操作員"""
        if str(user_id) not in self.data['operators']:
            self.data['operators'].append(str(user_id))
            self.save_data()
            return True
        return False

    def remove_operator(self, user_id):
        """移除操作員"""
        if str(user_id) in self.data['operators']:
            self.data['operators'].remove(str(user_id))
            self.save_data()
            return True
        return False

    def get_operators(self):
        """獲取所有操作員"""
        return self.data['operators']

    def clear_today_transactions(self):
        """清空今日交易記錄"""
        self.data['deposits'] = []
        self.data['withdrawals'] = []
        self.save_data()

    def clear_all_transactions(self):
        """清空所有交易記錄"""
        self.clear_today_transactions()

    def set_farewell_enabled(self, enabled):
        """設定是否啟用告別訊息"""
        self.data['farewell_enabled'] = enabled
        self.save_data()

    def get_farewell_enabled(self):
        """獲取告別訊息啟用狀態"""
        return self.data.get('farewell_enabled', True)

    def set_farewell_message(self, message):
        """設定告別詞"""
        self.data['farewell_message'] = message
        self.save_data()

    def get_farewell_message(self):
        """獲取告別詞"""
        return self.data.get('farewell_message', '👋 {SURNAME} 已離開群組，期待再相會！')

    def get_rate_by_date(self, date_str):
        """取得指定日期的匯率，若無則回傳全域預設匯率"""
        rates_by_date = self.data.get('rates_by_date', {})
        rate = rates_by_date.get(date_str)
        if rate:
            return rate
        # fallback to global
        return self.data['rates']

    def set_rate_by_date(self, date_str, deposit_rate=None, withdrawal_rate=None):
        """設定指定日期的匯率"""
        if 'rates_by_date' not in self.data:
            self.data['rates_by_date'] = {}
        if date_str not in self.data['rates_by_date']:
            self.data['rates_by_date'][date_str] = {}
        if deposit_rate is not None:
            self.data['rates_by_date'][date_str]['deposit'] = float(deposit_rate)
        if withdrawal_rate is not None:
            self.data['rates_by_date'][date_str]['withdrawal'] = float(withdrawal_rate)
        self.save_data()

# 其他設定常數
API_TOKEN = '8150609743:AAHkPIDjAP_FRiCt-yRBwrh_SY_AqJIjvGQ'
GROUP_ID = -1002229824712

# 成員設定
MEMBERS = {
    "@Fanny_Orz": "Fanny_Orz",

}

# 管理員設定
ADMIN_USERS = {
    "@Fanny_Orz",  # Telegram 用戶名需加 @
    "@ysdghjqefd",  # Telegram 用戶名需加 @
    "@bxu8120",     # Telegram 用戶名需加 @
    "@qaz521888"    # Telegram 用戶名需加 @
}

# 群主設定
GROUP_OWNER = "Fanny_Orz"  # 替換成群主的 Telegram 用戶名（不需要加@）

# 檔案監控設定
MONITOR_EXTENSIONS = ['.py', '.json', '.txt']  # 要監控的檔案類型
CHECK_INTERVAL = 5  # 檢查間隔（秒）

# 備份設定
MAX_BACKUPS = 5
BACKUP_DIR = 'backups'

# 心跳檢測設定
HEARTBEAT_INTERVAL = 3600  # 1小時
CONNECTION_CHECK_INTERVAL = 300  # 5分鐘
MAX_CONNECTION_ERRORS = 3

# 匯率設定
DEFAULT_EXCHANGE_RATE_TW = 31.5  # 預設台幣對USDT匯率
DEFAULT_EXCHANGE_RATE_CN = 7.2   # 預設人民幣對USDT匯率

# 管理員權限設定
ADMIN_LEVELS = {
    "OWNER": {  # 群主權限
        "users": ["Fanny_Orz"],  # 群主的 Telegram 用戶名（不需要加@）
        "permissions": [
            "delete_data",      # 刪除數據權限
            "restart_bot",      # 重啟機器人權限
            "manage_admins",    # 管理其他管理員權限
            "set_exchange_rate",# 設定匯率權限
            "view_all_reports", # 查看所有報表權限
            "backup_data",      # 備份數據權限
            "restore_data"      # 恢復數據權限
        ]
    },
    "SUPER_ADMIN": {  # 超級管理員權限
        "users": [
            "ysdghjqefd",
            "bxu8120",
            "Fanny_Orz",
            "qaz521888",
        ],
        "permissions": [
            "delete_data",
            "restart_bot",
            "set_exchange_rate",
            "view_all_reports",
            "backup_data"
        ]
    },
    "ADMIN": {  # 一般管理員權限
        "users": [
        ],
        "permissions": [
            "set_exchange_rate",
            "view_all_reports"
        ]
    }
}

# 權限描述
PERMISSION_DESCRIPTIONS = {
    "delete_data": "刪除報表數據",
    "restart_bot": "重新啟動機器人",
    "manage_admins": "管理其他管理員",
    "set_exchange_rate": "設定匯率",
    "view_all_reports": "查看所有報表",
    "backup_data": "備份數據",
    "restore_data": "恢復數據備份"
}

# 向下相容的管理員列表（保留原有的 ADMIN_USERS）
ADMIN_USERS = (
    ADMIN_LEVELS["OWNER"]["users"] + 
    ADMIN_LEVELS["SUPER_ADMIN"]["users"] + 
    ADMIN_LEVELS["ADMIN"]["users"]
)

def extract_amount(keyword):
    after = text.split(keyword+"+", 1)[1]
    # 只抓第一組「可有正負號、可有小數點」的數字
    match = re.search(r"[-+]?\d[\d,]*\.?\d*", after)
    if not match:
        raise ValueError("金額格式錯誤")
    num_str = match.group().replace(",", "")
    return float(num_str)
