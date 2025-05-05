import telebot
import re
from datetime import datetime, timedelta
from config import Config
from accounting import Accounting
import json
import os
import logging
from collections import defaultdict
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import time

# 初始化機器人和配置
bot = telebot.TeleBot('8150609743:AAHkPIDjAP_FRiCt-yRBwrh_SY_AqJIjvGQ')
config = Config()
accounting = Accounting()

# 用戶狀態追踪
user_states = {}

# 聊天與用戶資訊
BOT_CHAT_ID = 7842840472
GROUP_CHAT_ID = -1002229824712
BOT_USER_NAME = "北金國際-M8P-Ann"
GROUP_TITLE = "North™Sea.ᴍ8ᴘ計算器"

# 新增一個全域字典追蹤等待摘要輸入的用戶
edit_summary_waiting = set()

# 設置日誌記錄
def setup_logging():
    """設置日誌記錄"""
    # 創建logs目錄（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 設置日誌文件名（使用當前日期）
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file = f'logs/bot_log_{current_date}.txt'
    
    # 配置日誌記錄器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('BotLogger')

# 創建日誌記錄器
logger = setup_logging()

def log_message(message, action_type="一般消息"):
    """記錄消息到日誌"""
    try:
        # 獲取基本信息
        user_id = message.from_user.id
        username = message.from_user.username or "未知用戶名"
        chat_id = message.chat.id
        chat_title = message.chat.title if message.chat.title else "私聊"
        message_text = message.text or "無文字內容"
        
        # 格式化日誌消息
        log_text = f"""
操作類型: {action_type}
用戶ID: {user_id}
用戶名: {username}
群組ID: {chat_id}
群組名: {chat_title}
消息內容: {message_text}
------------------------"""
        
        # 記錄到日誌
        logger.info(log_text)
    except Exception as e:
        logger.error(f"記錄消息時發生錯誤：{str(e)}")

# 創建鍵盤按鈕
def create_keyboard():
    return None

def create_admin_settings_keyboard():
    return None

def create_admin_inline_keyboard(chat_id):
    return None

def create_help_keyboard():
    return None

def create_welcome_settings_keyboard(is_enabled=True):
    return None

def create_farewell_settings_keyboard(is_enabled=True):
    return None

def create_scheduled_message_keyboard(is_enabled=True):
    return None

# 在檔案開頭區域加入全域變數
change_notify_enabled = True
file_change_notify_enabled = True

# 全域變數：等待刪除狀態
pending_delete_report = {}

def create_main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('📑歷史報表', callback_data='main_history'),
        InlineKeyboardButton('🗑️刪除報表', callback_data='main_delete'),
        InlineKeyboardButton('👮‍♂️權限管理', callback_data='main_admin'),
        InlineKeyboardButton('🔄️重新啟動', callback_data='main_restart')
    )
    markup.add(
        InlineKeyboardButton('👀使用說明', callback_data='main_help')
    )
    return markup

def create_report_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('🔺糖均總表', callback_data='report_tangjun'),
        InlineKeyboardButton('🔹杰倫總表', callback_data='report_jielun'),
        InlineKeyboardButton('🔺阿豪總表', callback_data='report_ahao'),
        InlineKeyboardButton('🔹ᴍ8ᴘ總表', callback_data='report_m8p')
    )
    return markup

def create_month_menu(base_month):
    from datetime import datetime, timedelta
    markup = InlineKeyboardMarkup(row_width=2)
    now = datetime.now()
    for i in range(1, 5):
        month = (now.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=30*(i-1))
        label = month.strftime(f'📅%m月份總表')
        markup.add(InlineKeyboardButton(label, callback_data=f'month_{month.strftime("%Y%m")}'))
    return markup

def create_delete_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('🔺糖均總表', callback_data='delete_tangjun'),
        InlineKeyboardButton('🔹杰倫總表', callback_data='delete_jielun'),
        InlineKeyboardButton('🔺阿豪總表', callback_data='delete_ahao'),
        InlineKeyboardButton('🔹ᴍ8ᴘ總表', callback_data='delete_m8p')
    )
    return markup


def handle_welcome_settings_callback(call, chat_id):
    """處理歡迎詞設定回調"""
    help_text = f"""👋 歡迎詞設定說明

目前歡迎詞：
{config.get_welcome_message()}

可用變數：
{{SURNAME}} - 新成員的用戶名
{{FULLNAME}} - 新成員的完整名稱
{{FIRSTNAME}} - 新成員的名字
{{GROUPNAME}} - 群組名稱

設定方式：
直接回覆 "設定歡迎詞：" 加上您要的歡迎詞內容
例如：設定歡迎詞：歡迎 {{SURNAME}} 加入我們！"""
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=help_text
    )

def handle_quick_commands_callback(call, chat_id):
    """處理快速指令回調"""
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=get_admin_commands_message()
    )

def handle_list_admins_callback(call, chat_id):
    """處理查看管理員回調"""
    try:
        admins = bot.get_chat_administrators(chat_id)
        admin_list = "📋 群組管理員列表：\n\n"
        for admin in admins:
            user = admin.user
            status = "👑 群主" if admin.status == "creator" else "👮‍♂️ 管理員"
            admin_list += f"{status}：@{user.username or user.first_name}\n"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=admin_list
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ 獲取管理員列表時發生錯誤：{str(e)}")

def handle_list_operators_callback(call, chat_id):
    """處理查看操作員回調"""
    try:
        operators = config.get_operators()
        if not operators:
            operator_list = "目前沒有設定任何操作員"
        else:
            operator_list = "🔍 操作員列表：\n\n"
            for operator_id in operators:
                try:
                    user = bot.get_chat_member(chat_id, operator_id).user
                    operator_list += f"@{user.username or user.first_name}\n"
                except:
                    operator_list += f"ID: {operator_id}\n"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=operator_list
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ 獲取操作員列表時發生錯誤：{str(e)}")

def format_time(time_str):
    """格式化時間為 HHMM 格式"""
    if not time_str:
        return ''
    
    # 移除所有空格
    time_str = time_str.strip()
    
    # 處理 "4月16日 下午：16:30" 這樣的格式
    date_time_match = re.search(r'\d+月\d+日.*?(\d{1,2})[.:：](\d{2})', time_str)
    if date_time_match:
        hour = int(date_time_match.group(1))
        minute = int(date_time_match.group(2))
        return f"{hour:02d}:{minute:02d}"
    
    # 處理 "下午16:30" 或 "16:30" 格式
    time_match = re.search(r'(?:[上下午早晚]午?\s*)?(\d{1,2})[.:：](\d{2})', time_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        return f"{hour:02d}:{minute:02d}"
    
    return time_str

def format_customer_name(name):
    """格式化客戶名稱"""
    if not name:
        return ''
    name = name.strip()
    # 如果只有一個字
    if len(name) == 1:
        return f"{name}先生/小姐"
    return name

def format_company_name(name):
    """格式化公司名稱（取前四個字）"""
    if not name:
        return ''
    # 移除空格並取前四個字
    name = name.strip()
    return name[:4]

def format_amount(amount_str):
    """格式化金額為 XX.X萬 格式"""
    if not amount_str:
        return '0.0'
    
    # 移除所有空格和逗號
    amount_str = amount_str.replace(' ', '').replace(',', '')
    
    # 處理帶有"萬"字的情況
    if '萬' in amount_str:
        amount_str = amount_str.replace('萬', '')
        try:
            return f"{float(amount_str):.1f}"
        except ValueError:
            return '0.0'
    
    # 處理一般數字
    try:
        amount = float(amount_str)
        # 轉換為萬為單位
        return f"{amount/10000:.1f}"
    except ValueError:
        return '0.0'

def extract_district(address):
    """提取地址中的縣市區鄉鎮"""
    if not address:
        return ''
    
    # 統一將台改為臺
    address = address.replace('台', '臺')
    
    # 匹配完整的縣市區鄉鎮格式
    match = re.search(r'([臺台][北中南東西][市縣])([^市縣]{1,3}[區鄉鎮市])', address)
    if match:
        city = match.group(1).replace('臺', '台')
        district = match.group(2)
        return f"{city}{district}"
    
    return address

def find_company_name(text):
    """從文本中搜尋公司名稱"""
    if not text:
        return ''
    
    # 搜尋包含"有限公司"或"股份有限公司"的完整名稱
    company_patterns = [
        r'([^\n\r]+?股份有限公司)',  # 匹配股份有限公司
        r'([^\n\r]+?有限公司)',      # 匹配一般有限公司
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text)
        if match:
            company_name = match.group(1).strip()
            # 如果公司名稱超過4個字，只取前4個字
            if len(company_name) > 4:
                return company_name[:4]
            return company_name
    
    return ''

def extract_information(text, field_names):
    """從文本中提取指定字段的信息"""
    if not text:
        return ''
    
    # 按行搜索
    lines = text.split('\n')
    for line in lines:
        for field_name in field_names:
            # 處理帶數字編號的格式（如：1.客戶名稱、2.電話）
            field_pattern = f'(?:(?:\\d+\\.)?{field_name}|{field_name})[:：]\\s*'
            match = re.search(field_pattern, line)
            if match:
                value = line[match.end():].strip()
                return value
    
    # 如果是在找公司名稱且沒有找到，嘗試自動搜尋
    if '公司名稱' in field_names:
        return find_company_name(text)
    
    return ''

@bot.message_handler(func=lambda message: message.text == '列表' and message.reply_to_message)
def handle_list_command(message):
    """處理列表命令"""
    original_text = message.reply_to_message.text
    if not original_text:
        return

    # 提取各項信息
    company_name = format_company_name(extract_information(original_text, ['公司名稱']))
    customer_name = format_customer_name(extract_information(original_text, ['客戶名稱', '客戶姓名', '客戶', '姓名', '姓名：']))
    
    # 處理金額，支援"X萬"格式
    amount_text = extract_information(original_text, ['收款金額', '儲值金額', '額度', '金額', '存入操作金額'])
    amount = format_amount(amount_text)
    
    # 處理時間
    time = format_time(extract_information(original_text, ['時間', '收款時間', '預約時間', '日期時間']))
    
    # 處理地址
    address = extract_district(extract_information(original_text, ['公司地址', '預約地址', '收款地址', '收款地點', '交易地點', '地點']))

    # 格式化消息
    formatted_message = f'{time}【{company_name}-{amount}萬】{customer_name}【{address}】'

    # 發送格式化消息
    bot.reply_to(message, formatted_message)

def format_summary(amount, rate):
    """格式化金額和USDT"""
    try:
        amount = float(amount)
        rate = float(rate)
        usdt = amount / rate if rate > 0 else 0
        return f"{amount:,.0f} | {usdt:.2f}(USDT)"
    except (ValueError, TypeError):
        return "0 | 0.00(USDT)"

def get_member_title(user_id, username, phone=None):
    # 根據成員資訊決定總表標題
    if username == 'Fanny_Orz':
        return '糖均總表'
    elif username == 'ysdghjqefd':
        return '杰倫總表'
    elif phone == '+855 96 206 9845':
        return '阿豪總表'
    elif username == 'qaz521888':
        return 'ᴍ8ᴘ總表'
    else:
        return '成員總表'

# 取得本月所有日期（MM/DD 格式）
def get_month_dates():
    from datetime import date, timedelta
    today = date.today()
    first = today.replace(day=1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    days = (next_month - first).days
    return [(first + timedelta(days=i)).strftime('%m/%d (%a)') for i in range(days)]

# 依日期與幣別彙總金額
def summarize_by_date_and_currency(transactions):
    result = defaultdict(lambda: {'TWD': 0, 'CNY': 0})
    for t in transactions:
        # 取得日期（MM/DD）
        dt = datetime.strptime(t['time'], '%H:%M')
        # 假設有日期欄位，否則用今天
        date_str = t.get('date') or datetime.now().strftime('%m/%d')
        currency = t.get('currency', 'TWD')
        result[date_str][currency] += abs(t['amount'])
    return result

# 產生總表訊息
def get_transaction_message(message=None):
    try:
        summary = config.get_transaction_summary()
        deposits = summary['deposits']
        username = message.from_user.username if message and message.from_user else ''
        user_id = message.from_user.id if message and message.from_user else ''
        from datetime import datetime
        now = datetime.now()
        month = now.strftime('%m')
        today = now.strftime('%d')
        week_map = {'Mon': '一', 'Tue': '二', 'Wed': '三', 'Thu': '四', 'Fri': '五', 'Sat': '六', 'Sun': '日'}
        weekday = week_map[now.strftime('%a')]
        title = get_member_title(user_id, username)
        # 產生本月所有日期（MM/DD (X)）
        def get_month_dates_chinese():
            from datetime import date, timedelta
            today = date.today()
            first = today.replace(day=1)
            next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
            days = (next_month - first).days
            week_map = {'Mon': '一', 'Tue': '二', 'Wed': '三', 'Thu': '四', 'Fri': '五', 'Sat': '六', 'Sun': '日'}
            result = []
            for i in range(days):
                d = first + timedelta(days=i)
                week = week_map[d.strftime('%a')]
                result.append(f"{d.strftime('%m/%d')} ({week})")
            return result
        month_dates = get_month_dates_chinese()
        from collections import defaultdict
        daily_sum = defaultdict(lambda: {'TWD': 0, 'CNY': 0})
        # 將每筆交易的 date_str 也轉成 MM/DD (X) 格式
        for t in deposits:
            if t.get('username', '') != username:
                continue
            # 只統計本月的
            d = t.get('date') or now.strftime('%m/%d')
            try:
                y = now.year
                if '/' in d:
                    m, dd = d.split('/')
                    if m != month:
                        continue  # 只統計本月
                    dt = datetime(y, int(m), int(dd))
                    week = week_map[dt.strftime('%a')]
                    date_str = f"{dt.strftime('%m/%d')} ({week})"
                else:
                    date_str = d
            except:
                date_str = d
            currency = t.get('currency', 'TWD')
            daily_sum[date_str][currency] += abs(t['amount'])
        # 僅統計本月所有入款（deposit）
        total_twd = sum(t['amount'] for t in deposits if t.get('username','')==username and t.get('currency')=='TWD' and t.get('amount',0)>0 and (t.get('date','').startswith(month)))
        total_cny = sum(t['amount'] for t in deposits if t.get('username','')==username and t.get('currency')=='CNY' and t.get('amount',0)>0 and (t.get('date','').startswith(month)))
        rates = config.get_rates()
        tw_rate = float(rates.get('deposit', 1))
        cn_rate = float(rates.get('withdrawal', 1))
        usdt_tw = total_twd / tw_rate if tw_rate else 0
        usdt_cn = total_cny / cn_rate if cn_rate else 0
        public_usdt = 0
        private_usdt = 0
        custom = config.get_custom_summary(user_id)
        if custom:
            try:
                context = {
                    'title': title,
                    'total_twd': total_twd,
                    'total_cny': total_cny,
                    'usdt_tw': usdt_tw,
                    'usdt_cn': usdt_cn,
                    'public_usdt': public_usdt,
                    'private_usdt': private_usdt,
                    'month': month,
                    'today': today,
                    'weekday': weekday,
                }
                return custom.format(**context)
            except Exception as e:
                return f"摘要格式錯誤：{e}\n原始內容：\n{custom}"
        # 專屬格式 for @qaz521888
        if username == 'qaz521888':
            msg = ''
            msg += f"💰ᴛᴡ業績總額 = 每日ᴛᴡ總額｜ᴜsᴅᴛ$\n"
            msg += f"💰ᴄɴ業績總額 = 每日ᴄɴ總額｜ᴜsᴅᴛ$\n"
            msg += f"©️公桶 ᴜsᴅᴛ$\n"
            msg += f"————————————————————————\n"
            # 取得三個username
            m8p_usernames = ['Fanny_Orz', 'ysdghjqefd', 'bxu8120']
            # 先彙總三人每日金額
            m8p_daily_sum = defaultdict(lambda: {'TWD': 0, 'CNY': 0})
            for t in deposits:
                if t.get('username', '') not in m8p_usernames:
                    continue
                d = t.get('date') or now.strftime('%m/%d')
                try:
                    y = now.year
                    if '/' in d:
                        m, dd = d.split('/')
                        if m != month:
                            continue
                        dt = datetime(y, int(m), int(dd))
                        week = week_map[dt.strftime('%a')]
                        date_str = f"{dt.strftime('%m/%d')} ({week})"
                    else:
                        date_str = d
                except:
                    date_str = d
                currency = t.get('currency', 'TWD')
                m8p_daily_sum[date_str][currency] += abs(t['amount'])
            # 每日明細
            for d in month_dates:
                date_part, week_part = d.split(' ')
                rate_obj = config.get_rate_by_date(date_part)
                tw_rate_str = f"{rate_obj.get('deposit','')}" if rate_obj.get('deposit') else ''
                cn_rate_str = f"{rate_obj.get('withdrawal','')}" if rate_obj.get('withdrawal') else ''
                twd = m8p_daily_sum[d]['TWD']
                cny = m8p_daily_sum[d]['CNY']
                usdt = 0
                try:
                    tw_rate = float(rate_obj.get('deposit', 0) or 0)
                    cn_rate = float(rate_obj.get('withdrawal', 0) or 0)
                    usdt = (twd / tw_rate if tw_rate else 0) + (cny / cn_rate if cn_rate else 0)
                except:
                    usdt = 0
                msg += f"{date_part} {week_part} ᴛᴡ匯率[{tw_rate_str}] ∥ ᴄɴ匯率[{cn_rate_str}]\n"
                msg += f"ɴᴛᴅ${twd:,} ∥ ᴄɴʏ¥{cny:,}｜ᴜsᴅᴛ${usdt:.2f}\n"
            return msg.strip()
        # 其他成員維持原本格式
        msg = f"【{title}】\n"
        msg += f"💰ᴛᴡ業績總額\u3000ɴᴛᴅ${total_twd:,}\u3000｜ᴜsᴅᴛ${usdt_tw:,.2f}\n"
        msg += f"💰ᴄɴ業績總額\u3000ᴄɴʏ¥{total_cny:,}\u3000｜ᴜsᴅᴛ${usdt_cn:,.2f}\n"
        msg += f"©️公桶\u3000ᴜsᴅᴛ${public_usdt}\n"
        msg += f"©️私人\u3000ᴜsᴅᴛ${private_usdt}\n"
        msg += "——————————————\n"
        for d in month_dates:
            twd = daily_sum[d]['TWD']
            cny = daily_sum[d]['CNY']
            msg += f"{d}\nɴᴛᴅ${twd:,}\u3000∥\u3000ᴄɴʏ¥{cny:,}\n"
        return msg.strip()
    except Exception as e:
        return f"產生總表時發生錯誤：{str(e)}"

def get_history_message():
    """生成歷史帳單消息，顯示幣別"""
    try:
        summary = config.get_transaction_summary()
        message = "📜 歷史帳單：\n\n"
        # 顯示所有入款記錄
        message += "🟢入款記錄：\n"
        if summary['deposits']:
            for deposit in summary['deposits']:
                time = format_time(deposit['time'])
                currency = deposit.get('currency', 'TWD')
                message += f"{time} +{deposit['amount']:,.0f} {currency}\n"
        else:
            message += "暫無入款記錄\n"
        # 顯示所有出款記錄
        message += "\n🔴出款記錄：\n"
        if summary['withdrawals']:
            for withdrawal in summary['withdrawals']:
                time = format_time(withdrawal['time'])
                currency = withdrawal.get('currency', 'TWD')
                message += f"{time} -{abs(withdrawal['amount']):,.0f} {currency}\n"
        else:
            message += "暫無出款記錄\n"
        return message
    except Exception as e:
        print(f"生成歷史帳單時發生錯誤：{str(e)}")
        return "生成歷史帳單時發生錯誤"

def get_admin_help_message():
    """生成管理員使用說明"""
    return """北金 North™Sea ᴍ8ᴘ 專屬機器人
-----------------------------------------------
僅限群組主或群組管理員使用

🔴設定操作員 @xxxxx @ccccc
🔴查看操作員
🔴刪除操作員 @xxxxx @ccccc
🔴刪除帳單
🔴刪除歷史帳單 慎用
-----------------------------------------------
群組主或者群組管理員或操作人

🔴設定入款匯率33.25
🔴設定出款匯率33.25

🟢 入款操作
🔹 +1000

🟢 出款普通金額
🔹 -1000

🔴修正命令 入款-100 出款-100
🔴入款撤銷 撤銷最近一筆入款帳單
🔴出款撤銷 撤銷最近一筆出款帳單
🔴+0  顯示帳單

🟢 計算器
🔹 (500+600)*8+(600-9)/5
🔹 500+600+800/85

🔴設定群發廣播 群發廣播訊息
🔴取消群發廣播 取消群發廣播訊息
🔺刪除所有聊天室訊息
🔺刪除所有非置頂訊息"""

def get_operator_help_message():
    """生成操作人使用說明"""
    return """北金 North™Sea ᴍ8ᴘ 專屬機器人
-----------------------------------------------

🟢 計算器
🔹 (500+600)*8+(600-9)/5
🔹 500+600+800/85

🔴 列表
在要列表的文字訊息回覆 "列表" 就會自動幫您把格式列表完畢囉！"""

@bot.message_handler(func=lambda message: message.text == '👀使用說明')
def handle_usage_guide(message):
    guide = (
        '1️⃣TW+999999\n'
        '2️⃣CN+999999\n'
        '3️⃣公桶+300\n'
        '4️⃣私人+300\n'
        '5️⃣設定匯率TW33.33\n'
        '6️⃣設定匯率CN33.33\n'
        '7️⃣重啟\n'
        '⚠️以上指令都有 ± 功能，自行變通。'
    )
    bot.reply_to(message, guide)

@bot.message_handler(func=lambda message: message.text == '👮‍♂️管理員按鈕')
def handle_admin_help(message):
    """處理管理員說明請求"""
    bot.reply_to(message, get_admin_help_message())

@bot.message_handler(func=lambda message: message.text == '✏️操作人按鈕')
def handle_operator_help(message):
    """處理操作人說明請求"""
    bot.reply_to(message, get_operator_help_message())

@bot.message_handler(func=lambda message: message.text and message.text.startswith('[') and message.text.endswith(']'))
def handle_command(message):
    """處理命令"""
    # 移除方括號
    command = message.text[1:-1]
    bot.reply_to(message, f"執行命令：{command}")

def is_valid_calculation(text):
    """檢查是否為有效的計算公式"""
    # 移除所有空格和逗號
    text = text.replace(' ', '').replace(',', '')
    
    # 如果以+或-開頭，直接返回False（這是記帳功能）
    if text.startswith('+') or text.startswith('-'):
        return False
    
    # 檢查是否包含運算符
    operators = '+-*/'
    operator_count = sum(text.count(op) for op in operators)
    if operator_count == 0:
        return False
    
    # 檢查括號是否配對
    brackets_count = 0
    for c in text:
        if c == '(':
            brackets_count += 1
        elif c == ')':
            brackets_count -= 1
        if brackets_count < 0:  # 右括號多於左括號
            return False
    
    # 檢查是否只包含合法字符
    valid_chars = set('0123456789.+-*/() ')
    if not all(c in valid_chars for c in text):
        return False
    
    # 檢查數字的數量（至少需要兩個數字）
    numbers = [n for n in re.split(r'[+\-*/() ]+', text) if n]
    if len(numbers) < 2:
        return False
    
    # 檢查每個數字是否有效
    try:
        for num in numbers:
            if num:
                float(num)
        return True
    except ValueError:
        return False

def evaluate_expression(expression):
    """計算數學表達式"""
    try:
        # 基本安全檢查：只允許數字和基本運算符
        if not all(c in '0123456789.+-*/() ' for c in expression):
            return None
            
        # 計算結果
        result = eval(expression)
        
        # 如果結果是整數，返回整數格式
        if isinstance(result, (int, float)):
            if result.is_integer():
                return int(result)
            return round(result, 2)
        return None
    except:
        return None

@bot.message_handler(func=lambda message: message.text and is_valid_calculation(message.text))
def handle_calculator(message):
    """處理計算器功能"""
    try:
        # 移除所有逗號和空格
        expression = message.text.replace(',', '').replace(' ', '')
        
        # 檢查是否為有效的計算表達式
        if not is_valid_calculation(expression):
            return  # 如果不是有效的計算表達式，直接返回（可能是記帳功能）
        
        # 計算結果
        result = evaluate_expression(expression)
        
        if result is not None:
            # 格式化大數字（加上千位分隔符）
            if isinstance(result, (int, float)):
                formatted_result = format(result, ',')
                bot.reply_to(message, f"{message.text} = {formatted_result}")
        else:
            return  # 如果計算失敗，直接返回（可能是記帳功能）
    except Exception as e:
        return  # 如果發生錯誤，直接返回（可能是記帳功能）

@bot.message_handler(func=lambda message: message.text == '📜歷史帳單')
def handle_history(message):
    """處理歷史帳單請求"""
    bot.reply_to(message, get_history_message())

@bot.message_handler(func=lambda message: message.text and message.text.startswith('+'))
def handle_deposit(message):
    """處理入款操作"""
    try:
        # 從消息中提取金額
        amount_str = message.text.strip()[1:]  # 移除 '+' 符號
        # 移除所有逗號
        amount_str = amount_str.replace(',', '')
        amount = float(amount_str)
        
        # 添加交易記錄
        config.add_transaction(amount, 'deposit')
        
        # 回覆完整交易摘要
        bot.reply_to(message, get_transaction_message())
    except ValueError:
        bot.reply_to(message, "❌ 格式錯誤！請使用：+金額")
    except Exception as e:
        bot.reply_to(message, f"❌ 處理入款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('-'))
def handle_withdrawal(message):
    """處理出款操作"""
    try:
        # 從消息中提取金額
        amount_str = message.text.strip()[1:]  # 移除 '-' 符號
        # 移除所有逗號
        amount_str = amount_str.replace(',', '')
        amount = float(amount_str)
        
        # 添加交易記錄
        config.add_transaction(amount, 'withdrawal')
        
        # 回覆完整交易摘要
        bot.reply_to(message, get_transaction_message())
    except ValueError:
        bot.reply_to(message, "❌ 格式錯誤！請使用：-金額")
    except Exception as e:
        bot.reply_to(message, f"❌ 處理出款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '刪除帳單')
def handle_clear_today(message):
    """處理刪除今日帳單的請求"""
    try:
        # 記錄操作
        log_message(message, "刪除今日帳單")
        
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return
        
        config.clear_today_transactions()
        bot.reply_to(message, "✅ 已清空今日帳單")
    except Exception as e:
        bot.reply_to(message, f"❌ 清空今日帳單時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '刪除歷史帳單')
def handle_clear_history(message):
    """處理刪除歷史帳單的請求"""
    try:
        # 記錄操作
        log_message(message, "刪除歷史帳單")
        
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return
        
        config.clear_all_transactions()
        bot.reply_to(message, "✅ 已清空所有歷史帳單")
    except Exception as e:
        bot.reply_to(message, f"❌ 清空歷史帳單時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定入款匯率'))
def handle_set_deposit_rate(message):
    """處理設定入款匯率的請求"""
    try:
        # 記錄操作
        log_message(message, "設定入款匯率")
        
        # 檢查權限
        if not (is_admin(message.from_user.id, message.chat.id) or is_operator(message.from_user.id)):
            bot.reply_to(message, "❌ 此命令僅限管理員或操作員使用")
            return
        
        # 提取匯率數值
        rate = float(message.text.replace('設定入款匯率', '').strip())
        config.set_deposit_rate(rate)
        bot.reply_to(message, f"✅ 已設定入款匯率為：{rate}")
    except ValueError:
        bot.reply_to(message, "❌ 匯率格式錯誤！請使用正確的數字格式")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定入款匯率時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('設定出款匯率'))
def handle_set_withdrawal_rate(message):
    """處理設定出款匯率的請求"""
    try:
        # 記錄操作
        log_message(message, "設定出款匯率")
        
        # 檢查權限
        if not (is_admin(message.from_user.id, message.chat.id) or is_operator(message.from_user.id)):
            bot.reply_to(message, "❌ 此命令僅限管理員或操作員使用")
            return
        
        # 提取匯率數值
        rate = float(message.text.replace('設定出款匯率', '').strip())
        config.set_withdrawal_rate(rate)
        bot.reply_to(message, f"✅ 已設定出款匯率為：{rate}")
    except ValueError:
        bot.reply_to(message, "❌ 匯率格式錯誤！請使用正確的數字格式")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定出款匯率時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '入款撤銷')
def handle_cancel_last_deposit(message):
    """處理撤銷最後一筆入款的請求"""
    try:
        # 記錄操作
        log_message(message, "撤銷入款")
        
        # 檢查權限
        if not (is_admin(message.from_user.id, message.chat.id) or is_operator(message.from_user.id)):
            bot.reply_to(message, "❌ 此命令僅限管理員或操作員使用")
            return
        
        # 獲取交易摘要
        summary = config.get_transaction_summary()
        if not summary['deposits']:
            bot.reply_to(message, "❌ 沒有可撤銷的入款記錄")
            return
        
        # 獲取最後一筆入款金額用於顯示
        last_amount = summary['deposits'][-1]['amount']
        
        # 執行撤銷操作
        if config.cancel_last_deposit():
            bot.reply_to(message, f"✅ 已撤銷最後一筆入款：{last_amount:,.0f}")
            # 更新交易摘要
            bot.reply_to(message, get_transaction_message())
        else:
            bot.reply_to(message, "❌ 撤銷入款失敗")
    except Exception as e:
        bot.reply_to(message, f"❌ 撤銷入款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '出款撤銷')
def handle_cancel_last_withdrawal(message):
    """處理撤銷最後一筆出款的請求"""
    try:
        # 記錄操作
        log_message(message, "撤銷出款")
        
        # 檢查權限
        if not (is_admin(message.from_user.id, message.chat.id) or is_operator(message.from_user.id)):
            bot.reply_to(message, "❌ 此命令僅限管理員或操作員使用")
            return
        
        # 獲取交易摘要
        summary = config.get_transaction_summary()
        if not summary['withdrawals']:
            bot.reply_to(message, "❌ 沒有可撤銷的出款記錄")
            return
        
        # 獲取最後一筆出款金額用於顯示
        last_amount = abs(summary['withdrawals'][-1]['amount'])
        
        # 執行撤銷操作
        if config.cancel_last_withdrawal():
            bot.reply_to(message, f"✅ 已撤銷最後一筆出款：{last_amount:,.0f}")
            # 更新交易摘要
            bot.reply_to(message, get_transaction_message())
        else:
            bot.reply_to(message, "❌ 撤銷出款失敗")
    except Exception as e:
        bot.reply_to(message, f"❌ 撤銷出款時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '設定群發廣播')
def handle_enable_broadcast(message):
    """處理啟用群發廣播的請求"""
    try:
        # 記錄操作
        log_message(message, "啟用群發廣播")
        
        # 檢查權限
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return
        
        config.set_broadcast_mode(True)
        bot.reply_to(message, "✅ 已啟用群發廣播模式")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定群發廣播時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '取消群發廣播')
def handle_disable_broadcast(message):
    """處理取消群發廣播的請求"""
    try:
        # 記錄操作
        log_message(message, "取消群發廣播")
        
        # 檢查權限
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return
        
        config.set_broadcast_mode(False)
        bot.reply_to(message, "✅ 已取消群發廣播模式")
    except Exception as e:
        bot.reply_to(message, f"❌ 取消群發廣播時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🛠️修復機器人')
def handle_repair_bot(message):
    """處理修復機器人請求"""
    repair_message = "「你的機器人好像壞掉了？」 快來修復它！"
    support_link = "https://t.me/Fanny_Orz"
    
    # 創建帶有連結的消息
    response = f"{repair_message}\n\n聯繫技術支援：{support_link}"
    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: message.text == '刪除所有聊天室訊息')
def handle_delete_all_messages(message):
    """處理刪除所有聊天室訊息的請求"""
    try:
        # 記錄操作
        log_message(message, "刪除所有聊天室訊息")
        
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        # 獲取當前消息ID
        current_message_id = message.message_id
        
        # 從當前消息開始往前刪除
        for msg_id in range(current_message_id, 0, -1):
            try:
                bot.delete_message(message.chat.id, msg_id)
            except:
                continue
        
        # 發送成功消息（這條消息也會被刪除）
        bot.send_message(message.chat.id, "✅ 已清空所有聊天室訊息")
    except Exception as e:
        bot.reply_to(message, f"❌ 刪除訊息時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '刪除所有非置頂訊息')
def handle_delete_non_pinned_messages(message):
    """處理刪除所有非置頂訊息的請求"""
    try:
        # 記錄操作
        log_message(message, "刪除所有非置頂訊息")
        
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此命令僅限管理員使用")
            return

        # 獲取置頂消息
        try:
            pinned_message = bot.get_chat(message.chat.id).pinned_message
            pinned_message_id = pinned_message.message_id if pinned_message else None
        except:
            pinned_message_id = None

        # 獲取當前消息ID
        current_message_id = message.message_id
        
        # 從當前消息開始往前刪除非置頂消息
        for msg_id in range(current_message_id, 0, -1):
            try:
                # 跳過置頂消息
                if pinned_message_id and msg_id == pinned_message_id:
                    continue
                bot.delete_message(message.chat.id, msg_id)
            except:
                continue
        
        # 發送成功消息（這條消息也會被刪除）
        bot.send_message(message.chat.id, "✅ 已清空所有非置頂訊息")
    except Exception as e:
        bot.reply_to(message, f"❌ 刪除訊息時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '+0')
def handle_show_summary(message):
    """處理顯示交易摘要的請求"""
    try:
        # 記錄操作
        log_message(message, "查看交易摘要")
        
        # 獲取並發送交易摘要
        summary = get_transaction_message()
        bot.reply_to(message, summary)
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取交易摘要時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text and (message.text.startswith('+') or message.text.startswith('-')))
def handle_transaction(message):
    """處理入款和出款操作"""
    try:
        # 記錄操作
        log_message(message, "入款" if message.text.startswith('+') else "出款")
        
        # 判斷是入款還是出款
        is_deposit = message.text.startswith('+')
        action_type = "入款" if is_deposit else "出款"
        
        # 提取金額
        amount_str = message.text[1:].replace(',', '')
        try:
            amount = float(amount_str)
        except ValueError:
            bot.reply_to(message, "❌ 金額格式錯誤！")
            return
        
        # 添加交易記錄
        config.add_transaction(amount, 'deposit' if is_deposit else 'withdrawal')
        
        # 發送交易摘要
        bot.reply_to(message, get_transaction_message())
    except Exception as e:
        bot.reply_to(message, f"❌ 處理{'入' if is_deposit else '出'}款時發生錯誤：{str(e)}")

def is_admin(user_id, chat_id):
    """檢查用戶是否為群組管理員或群主"""
    try:
        member = bot.get_chat_member(chat_id, user_id)
        # 如果是群主，直接返回 True
        if member.status == 'creator':
            return True
        # 如果是管理員，檢查是否有適當的權限
        elif member.status == 'administrator':
            return member.can_restrict_members and member.can_delete_messages
        return False
    except:
        return False

def is_operator(user_id):
    """檢查用戶是否為操作員"""
    try:
        return config.is_operator(user_id)
    except:
        return False

def is_group_owner(user_id, chat_id):
    """檢查用戶是否為群主"""
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status == 'creator'
    except:
        return False

def get_rules_message():
    """獲取群組規章內容"""
    return """北金 North™Sea ᴍ8ᴘ 群組規章
------------------------------------
1️⃣ 平時與業務的對話紀錄，請務必收回確實！乾淨！請勿將盤口、客戶指定地點等等之相關對話留存。務必要確實收回徹底。

2️⃣ 1號業務掛線內容確實，裝袋前務必再次清點金額。確認後在綁袋，若是自行後交外務主管，全程錄影直到給與外務主管。
2號3號業務相同。全程錄影直到給與外務主管or幣商，才可將視頻關閉。

3️⃣ 若隔日晨間有預約單，務必確實設定鬧鐘，並且打電話叫人員起床。"""

@bot.message_handler(func=lambda message: message.text == '📝群組規章')
def handle_rules(message):
    """處理群組規章請求"""
    try:
        # 記錄操作
        log_message(message, "查看群組規章")
        
        # 發送群組規章
        bot.reply_to(message, get_rules_message())
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取群組規章時發生錯誤：{str(e)}")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message):
    """處理新成員加入群組"""
    try:
        for new_member in message.new_chat_members:
            # 獲取新成員信息
            surname = new_member.username or f"{new_member.first_name} {new_member.last_name}".strip()
            fullname = f"{new_member.first_name} {new_member.last_name}".strip()
            firstname = new_member.first_name
            groupname = message.chat.title
            
            # 獲取歡迎詞模板
            welcome_template = config.get_welcome_message()
            
            # 替換變數
            welcome_message = welcome_template.format(
                SURNAME=surname,
                FULLNAME=fullname,
                FIRSTNAME=firstname,
                GROUPNAME=groupname
            )
            
            # 發送歡迎消息
            bot.reply_to(message, welcome_message)
            
            # 記錄操作
            log_message(message, f"新成員加入：{surname}")
    except Exception as e:
        logger.error(f"處理新成員加入時發生錯誤：{str(e)}")

def get_admin_commands_message():
    """獲取管理員命令列表"""
    return """🔰 群組管理員命令列表：

👮‍♂️ 管理員命令：
/ban @用戶名 [時間] [原因] - 禁言用戶（時間格式：1h, 1d, 1w）
/unban @用戶名 - 解除禁言
/kick @用戶名 [原因] - 踢出用戶
/warn @用戶名 [原因] - 警告用戶
/unwarn @用戶名 - 移除警告
/warns @用戶名 - 查看警告次數
/info @用戶名 - 查看用戶資訊
/del - 回覆要刪除的訊息即可刪除

⚠️ 注意：請謹慎使用管理命令"""

@bot.message_handler(func=lambda message: message.text == '👋 歡迎訊息')
def handle_welcome_message(message):
    """處理歡迎訊息設定"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        is_enabled = config.get_welcome_message_status()
        help_text = f"""👋 歡迎訊息設定

從此選單中，您可以設定當有人進入群組時將在群組中發送的歡迎訊息。
狀態: {'✅開啟' if is_enabled else '❎關閉'}

可用變數：
{{SURNAME}} - 新成員的用戶名
{{FULLNAME}} - 新成員的完整名稱
{{FIRSTNAME}} - 新成員的名字
{{GROUPNAME}} - 群組名稱"""
        
        bot.reply_to(message, help_text)
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示歡迎訊息設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '👋🏻 告別模板')
def handle_farewell_template(message):
    """處理告別模板設定"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        is_enabled = config.get_farewell_message_status()
        help_text = f"""👋🏻 告別模板設定

從此選單中，您可以設定當有人離開群組時將在群組中發送的告別訊息。
狀態: {'✅開啟' if is_enabled else '❎關閉'}

可用變數：
{{SURNAME}} - 離開成員的用戶名
{{FULLNAME}} - 離開成員的完整名稱
{{FIRSTNAME}} - 離開成員的名字
{{GROUPNAME}} - 群組名稱"""
        
        bot.reply_to(message, help_text)
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示告別模板設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '⏰ 排程訊息')
def handle_scheduled_message(message):
    """處理排程訊息設定"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        is_enabled = config.get_scheduled_message_status()
        help_text = f"""⏰ 排程訊息設定

從此選單中，您可以設定每隔幾分鐘/幾小時或每隔幾個訊息重複發送給群組的訊息。
狀態: {'✅開啟' if is_enabled else '❎關閉'}"""
        
        bot.reply_to(message, help_text)
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示排程訊息設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🚮刪除訊息')
def handle_delete_messages(message):
    """處理刪除訊息功能"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        help_text = """🚮 刪除訊息功能

1. 刪除單一訊息：
   回覆要刪除的訊息，並輸入 /del

2. 刪除所有訊息：
   點擊 "刪除所有聊天室訊息" 按鈕

3. 刪除非置頂訊息：
   點擊 "刪除所有非置頂訊息" 按鈕"""
        
        bot.reply_to(message, help_text)
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示刪除訊息功能時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '👮‍♂️ 查看管理員')
def handle_view_admins(message):
    """處理查看管理員列表"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        # 獲取群組管理員列表
        admins = bot.get_chat_administrators(message.chat.id)
        
        admin_list = "📋 群組管理員列表：\n\n"
        for admin in admins:
            user = admin.user
            status = "👑 群主" if admin.status == "creator" else "👮‍♂️ 管理員"
            admin_list += f"{status}：@{user.username or user.first_name}\n"
        
        bot.reply_to(message, admin_list)
    except Exception as e:
        bot.reply_to(message, f"❌ 獲取管理員列表時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🔺所有指令查詢')
def handle_all_commands(message):
    """處理所有指令查詢"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        commands_text = """🔺 所有可用指令：

👮‍♂️ 管理員指令：
/ban @用戶名 [時間] [原因] - 禁言用戶
/unban @用戶名 - 解除禁言
/kick @用戶名 [原因] - 踢出用戶
/warn @用戶名 [原因] - 警告用戶
/unwarn @用戶名 - 移除警告
/warns @用戶名 - 查看警告次數
/info @用戶名 - 查看用戶資訊
/del - 刪除訊息

📝 群組設定：
設定歡迎詞：內容 - 設定歡迎訊息
設定告別詞：內容 - 設定告別訊息
設定排程：時間 內容 - 設定排程訊息
刪除排程：時間 - 刪除排程訊息

💰 記帳功能：
+金額 - 入款
-金額 - 出款
+0 - 查看交易摘要
刪除帳單 - 清空今日帳單
刪除歷史帳單 - 清空所有歷史帳單

🛠️ 其他功能：
設定入款匯率 - 設定入款匯率
設定出款匯率 - 設定出款匯率
入款撤銷 - 撤銷最後一筆入款
出款撤銷 - 撤銷最後一筆出款"""
        
        bot.reply_to(message, commands_text)
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示指令列表時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🇹🇼 語言設置')
def handle_language_settings(message):
    """處理語言設置"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        help_text = """🇹🇼 語言設置說明

目前支援的語言：
1. 繁體中文 (預設)
2. 簡體中文
3. English

設定方式：
回覆 "設定語言：語言代碼"
例如：設定語言：zh-TW"""
        
        bot.reply_to(message, help_text)
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示語言設置時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🔙 返回到群管功能')
def handle_return(message):
    """處理返回按鈕"""
    try:
        # 檢查是否為管理員
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        # 獲取用戶狀態
        user_state = user_states.get(message.from_user.id, {})
        
        # 如果是在歡迎訊息設定中
        if user_state.get('last_action') == 'welcome_settings':
            # 返回到群管功能選單
            keyboard = create_admin_settings_keyboard()
            bot.reply_to(message, get_admin_settings_message())
            return
            
        # 如果是在群組設定中
        keyboard = create_admin_settings_keyboard()
        bot.reply_to(message, get_admin_settings_message())
        
    except Exception as e:
        bot.reply_to(message, f"❌ 返回時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '👥 群組內設定')
def handle_group_settings(message):
    """處理群組內設定"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(
            KeyboardButton('👋 歡迎訊息'),
            KeyboardButton('👋🏻 告別模板')
        )
        keyboard.row(
            KeyboardButton('⏰ 排程訊息'),
            KeyboardButton('🚮刪除訊息')
        )
        keyboard.row(
            KeyboardButton('👮‍♂️ 查看管理員'),
            KeyboardButton('🔺所有指令查詢')
        )
        keyboard.row(
            KeyboardButton('🇹🇼 語言設置'),
            KeyboardButton('🔙返回')
        )
        
        bot.reply_to(message, "請選擇要設定的功能：", reply_markup=keyboard)
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示群組設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text == '🔒 私訊設定')
def handle_private_settings(message):
    """處理私訊設定"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        # 如果是在群組中
        if message.chat.type != 'private':
            # 保存用戶狀態
            user_states[message.from_user.id] = {
                'chat_id': message.chat.id,
                'chat_title': message.chat.title
            }
            
            # 發送私訊邀請
            try:
                keyboard = create_admin_inline_keyboard(message.chat.id)
                bot.send_message(
                    message.from_user.id,
                    f"🔧 群組管理設定 - {message.chat.title}\n\n" + get_admin_settings_message()
                )
                bot.reply_to(message, "🔒 為了安全起見，我已經在私訊中發送了設定選項，請查看您的私訊")
            except Exception as e:
                bot.reply_to(message, "❌ 無法發送私訊，請先點擊 @您的機器人 開始對話")
            return
        
        # 如果已經在私訊中
        if message.from_user.id in user_states:
            chat_id = user_states[message.from_user.id]['chat_id']
            keyboard = create_admin_inline_keyboard(chat_id)
            bot.reply_to(message, get_admin_settings_message())
        else:
            bot.reply_to(message, "❌ 請在群組中使用此功能")
    except Exception as e:
        bot.reply_to(message, f"❌ 顯示私訊設定時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text in ['✅開啟', '❎關閉'])
def handle_toggle_feature(message):
    """處理開啟/關閉功能的按鈕"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        # 獲取當前狀態
        if message.text == '✅開啟':
            new_status = True
        else:
            new_status = False
        
        # 根據用戶狀態設置相應的功能
        if user_states.get(message.from_user.id, {}).get('last_action') == 'welcome_settings':
            config.set_welcome_message_status(new_status)
            bot.reply_to(message, f"✅ 歡迎訊息已{'開啟' if new_status else '關閉'}")
        elif user_states.get(message.from_user.id, {}).get('last_action') == 'farewell_settings':
            config.set_farewell_message_status(new_status)
            bot.reply_to(message, f"✅ 告別模板已{'開啟' if new_status else '關閉'}")
        elif user_states.get(message.from_user.id, {}).get('last_action') == 'scheduled_settings':
            config.set_scheduled_message_status(new_status)
            bot.reply_to(message, f"✅ 排程訊息已{'開啟' if new_status else '關閉'}")
    except Exception as e:
        bot.reply_to(message, f"❌ 設定功能狀態時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text in ['✍️ 自訂訊息', '🚮 刪除舊的歡迎訊息'])
def handle_welcome_message_actions(message):
    """處理歡迎訊息的動作"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        if message.text == '✍️ 自訂訊息':
            user_states[message.from_user.id] = {'waiting_for': 'welcome_message'}
            bot.reply_to(message, "請輸入新的歡迎訊息內容：")
        elif message.text == '🚮 刪除舊的歡迎訊息':
            config.clear_welcome_message()
            bot.reply_to(message, "✅ 已刪除舊的歡迎訊息", 
                        reply_markup=create_welcome_settings_keyboard(config.get_welcome_message_status()))
    except Exception as e:
        bot.reply_to(message, f"❌ 處理歡迎訊息動作時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text in ['✍️ 自訂訊息', '🚮 刪除舊的告別訊息'])
def handle_farewell_message_actions(message):
    """處理告別訊息的動作"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        if message.text == '✍️ 自訂訊息':
            user_states[message.from_user.id] = {'waiting_for': 'farewell_message'}
            bot.reply_to(message, "請輸入新的告別訊息內容：")
        elif message.text == '🚮 刪除舊的告別訊息':
            config.clear_farewell_message()
            bot.reply_to(message, "✅ 已刪除舊的告別訊息", 
                        reply_markup=create_farewell_settings_keyboard(config.get_farewell_message_status()))
    except Exception as e:
        bot.reply_to(message, f"❌ 處理告別訊息動作時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: message.text in ['➕ 新增訊息', '🚮 刪除舊的排程訊息', '💭 1️⃣', '💭 2️⃣', '💭 3️⃣'])
def handle_scheduled_message_actions(message):
    """處理排程訊息的動作"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        if message.text == '➕ 新增訊息':
            user_states[message.from_user.id] = {'waiting_for': 'scheduled_message'}
            bot.reply_to(message, "請輸入新的排程訊息內容和時間（格式：時間 訊息內容）：")
        elif message.text == '🚮 刪除舊的排程訊息':
            config.clear_scheduled_messages()
            bot.reply_to(message, "✅ 已刪除所有排程訊息", 
                        reply_markup=create_scheduled_message_keyboard(config.get_scheduled_message_status()))
        elif message.text.startswith('💭'):
            message_number = message.text.split()[-1].strip('️⃣')
            if message_number.isdigit():
                message_number = int(message_number)
                scheduled_message = config.get_scheduled_message(message_number)
                if scheduled_message:
                    bot.reply_to(message, f"排程訊息 {message_number}：\n時間：{scheduled_message['time']}\n內容：{scheduled_message['content']}")
                else:
                    bot.reply_to(message, f"❌ 排程訊息 {message_number} 不存在")
            else:
                bot.reply_to(message, "❌ 無效的排程訊息編號")
                return
    except Exception as e:
        bot.reply_to(message, f"❌ 處理排程訊息動作時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('waiting_for') in ['welcome_message', 'farewell_message', 'scheduled_message'])
def handle_message_input(message):
    """處理用戶輸入的訊息內容"""
    try:
        if not is_admin(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 此功能僅限管理員使用")
            return
        
        waiting_for = user_states[message.from_user.id]['waiting_for']
        
        if waiting_for == 'welcome_message':
            config.set_welcome_message(message.text)
            bot.reply_to(message, "✅ 歡迎訊息已更新", 
                        reply_markup=create_welcome_settings_keyboard(config.get_welcome_message_status()))
        elif waiting_for == 'farewell_message':
            config.set_farewell_message(message.text)
            bot.reply_to(message, "✅ 告別訊息已更新", 
                        reply_markup=create_farewell_settings_keyboard(config.get_farewell_message_status()))
        elif waiting_for == 'scheduled_message':
            try:
                time, content = message.text.split(' ', 1)
                config.add_scheduled_message(time, content)
                bot.reply_to(message, "✅ 排程訊息已新增", 
                            reply_markup=create_scheduled_message_keyboard(config.get_scheduled_message_status()))
            except ValueError:
                bot.reply_to(message, "❌ 格式錯誤！請使用：時間 訊息內容")
        
        # 清除等待狀態
        del user_states[message.from_user.id]['waiting_for']
    except Exception as e:
        bot.reply_to(message, f"❌ 設定訊息時發生錯誤：{str(e)}")

@bot.message_handler(func=lambda m: m.text and m.text.strip() == '重啟')
def handle_restart(message):
    # 僅限管理員
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

# 幣別交易處理
@bot.message_handler(func=lambda message: message.text and (
    message.text.startswith('TW+') or message.text.startswith('CN+') or 
    message.text.startswith('TW-') or message.text.startswith('CN-')))
def handle_currency_transaction(message):
    try:
        # 判斷幣別與入/出款
        if message.text.startswith('TW+'):
            currency = 'TWD'
            action = 'deposit'
            amount_str = message.text[3:]
        elif message.text.startswith('CN+'):
            currency = 'CNY'
            action = 'deposit'
            amount_str = message.text[3:]
        elif message.text.startswith('TW-'):
            currency = 'TWD'
            action = 'withdrawal'
            amount_str = message.text[3:]
        elif message.text.startswith('CN-'):
            currency = 'CNY'
            action = 'withdrawal'
            amount_str = message.text[3:]
        else:
            return
        amount_str = amount_str.replace(',', '').strip()
        amount = float(amount_str)
        username = message.from_user.username if message.from_user else ''
        user_id = message.from_user.id if message.from_user else ''
        # 補上 date 欄位（MM/DD）
        from datetime import datetime
        today_str = datetime.now().strftime('%m/%d')
        config.add_transaction(amount, action, currency=currency, username=username, user_id=user_id, date=today_str)
        bot.reply_to(message, f"✅ 已記錄{'入款' if action=='deposit' else '出款'} {amount} {currency}")
        bot.reply_to(message, get_transaction_message(message))
    except ValueError:
        bot.reply_to(message, "❌ 金額格式錯誤！")
    except Exception as e:
        bot.reply_to(message, f"❌ 處理交易時發生錯誤：{str(e)}")

@bot.message_handler(commands=['start', 'menu'])
def show_main_menu(message):
    bot.send_message(message.chat.id, '請選擇功能：', reply_markup=create_main_menu())

@bot.message_handler(func=lambda m: m.text == '📑歷史報表')
def handle_history_report(message):
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, '❌ 僅限管理員使用')
        return
    msg = get_history_message()
    msg += get_current_month_report_message()
    bot.send_message(message.chat.id, msg, reply_markup=create_report_menu())

@bot.message_handler(func=lambda m: m.text == '🗑️刪除報表')
def handle_delete_report(message):
    if not is_admin(message.from_user.id, message.chat.id):
        bot.reply_to(message, '❌ 僅限管理員使用')
        return

@bot.message_handler(func=lambda m: m.text == '👀使用說明')
def handle_usage_guide(message):
    guide = (
        '1️⃣TW+999999\n'
        '2️⃣CN+999999\n'
        '3️⃣公桶+300\n'
        '4️⃣私人+300\n'
        '5️⃣設定匯率TW33.33\n'
        '6️⃣設定匯率CN33.33\n'
        '7️⃣重啟\n'
        '⚠️以上指令都有 ± 功能，自行變通。'
    )
    bot.reply_to(message, guide)

@bot.message_handler(func=lambda m: m.text == '✍️編輯摘要消息')
def handle_edit_summary(message):
    edit_summary_waiting.add(message.from_user.id)
    bot.reply_to(message, '⚠️請直接輸入要顯示的業績摘要消息（可包含格式）')

@bot.message_handler(func=lambda m: m.from_user and m.from_user.id in edit_summary_waiting)
def handle_summary_input(message):
    edit_summary_waiting.discard(message.from_user.id)
    config.set_custom_summary(message.from_user.id, message.text)
    bot.reply_to(message, f'✅ 已更新摘要消息：\n{message.text}')

@bot.callback_query_handler(func=lambda call: call.data.startswith('report_'))
def handle_report_menu(call):
    # 解析總表名稱
    report_map = {
        'report_tangjun': '糖均總表',
        'report_jielun': '杰倫總表',
        'report_ahao': '阿豪總表',
        'report_m8p': 'ᴍ8ᴘ總表',
    }
    report_key = call.data
    report_name = report_map.get(report_key)
    if not report_name:
        bot.answer_callback_query(call.id, '查無此總表')
        return
    # 檢查是否存在（此處可加檢查邏輯）
    bot.edit_message_text(f'請選擇月份：', call.message.chat.id, call.message.message_id, reply_markup=create_month_menu(None))

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_delete_menu(call):
    # 解析總表名稱
    report_map = {
        'delete_tangjun': '糖均總表',
        'delete_jielun': '杰倫總表',
        'delete_ahao': '阿豪總表',
        'delete_m8p': 'ᴍ8ᴘ總表',
    }
    report_key = call.data
    report_name = report_map.get(report_key)
    if not report_name:
        bot.answer_callback_query(call.id, '查無此總表')
        return
    try:
        # 記錄等待刪除狀態
        global pending_delete_report
        pending_delete_report = {
            'chat_id': call.message.chat.id,
            'user_id': call.from_user.id,
            'report_name': report_name,
            'timestamp': time.time()
        }
        bot.edit_message_text(f'⚠️ 確定要刪除「{report_name}」的所有數據嗎？\n此操作不可恢復！\n如果確定要刪除，請在 30 秒內回覆：確定刪除', call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.answer_callback_query(call.id, f'處理請求時發生錯誤：{e}')

@bot.message_handler(func=lambda m: m.text == '確定刪除')
def handle_confirm_delete(message):
    global pending_delete_report
    now = time.time()
    # 檢查是否有等待刪除狀態且未超時
    if not pending_delete_report:
        bot.reply_to(message, '❌ 沒有等待刪除的報表，請重新操作。')
        return
    if message.from_user.id != pending_delete_report.get('user_id'):
        bot.reply_to(message, '❌ 只有發起刪除的管理員可以確認刪除。')
        return
    if now - pending_delete_report['timestamp'] > 30:
        bot.reply_to(message, '❌ 刪除超時，請重新操作。')
        pending_delete_report = {}
        return
    report_name = pending_delete_report['report_name']
    # 執行刪除（這裡請根據你的 config 實作刪除報表的邏輯）
    try:
        # 假設 config 有 clear_report(report_name) 方法
        if hasattr(config, 'clear_report'):
            config.clear_report(report_name)
            bot.reply_to(message, f'✅ 已刪除「{report_name}」的所有數據！')
        else:
            bot.reply_to(message, f'（模擬）已刪除「{report_name}」的所有數據！')
        pending_delete_report = {}
    except Exception as e:
        bot.reply_to(message, f'❌ 刪除時發生錯誤：{e}')
        pending_delete_report = {}

@bot.message_handler(commands=['show_summary'])
def show_current_summary(message):
    summary = get_transaction_message(message)
    bot.reply_to(message, f'目前的摘要消息：\n{summary}')

@bot.message_handler(func=lambda m: m.text == '查看摘要')
def show_current_summary_text(message):
    summary = get_transaction_message(message)
    bot.reply_to(message, f'目前的摘要消息：\n{summary}')

# 確保 config 物件有 get_custom_summary/set_custom_summary 方法
if not hasattr(config, 'custom_summary'):
    config.custom_summary = {}
if not hasattr(config, 'set_custom_summary'):
    def set_custom_summary(user_id, text):
        config.custom_summary[str(user_id)] = text
    config.set_custom_summary = set_custom_summary
if not hasattr(config, 'get_custom_summary'):
    def get_custom_summary(user_id):
        return config.custom_summary.get(str(user_id), None)
    config.get_custom_summary = get_custom_summary

@bot.message_handler(func=lambda message: bool(re.match(r"@\w+ \d{1,2}/\d{1,2} ((TW|CN)\+[\d,]+|公桶\+[\d,]+|私人\+[\d,]+)", message.text or "")) or bool(re.match(r"@\w+ ((TW|CN)\+[\d,]+|公桶\+[\d,]+|私人\+[\d,]+)", message.text or "")))
def handle_admin_add_for_user(message):
    try:
        # 僅限群主
        if not is_group_owner(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 只有群主可以使用此指令")
            return
        # 支援 @用戶名 [日期] TW+金額、CN+金額、公桶+金額、私人+金額
        match = re.match(r"@(\w+)(?: (\d{1,2}/\d{1,2}))? ((TW|CN)\+|公桶\+|私人\+)([\d,]+)", message.text)
        if not match:
            bot.reply_to(message, "❌ 格式錯誤，請用 @用戶名 [MM/DD] TW+金額 / CN+金額 / 公桶+金額 / 私人+金額")
            return
        target_username = match.group(1)
        date_str = match.group(2)
        type_prefix = match.group(3)
        amount_str = match.group(5).replace(',', '')
        amount = float(amount_str)
        # 只查管理員
        target_user_id = None
        try:
            admins = bot.get_chat_administrators(message.chat.id)
            for m in admins:
                if m.user.username and m.user.username.lower() == target_username.lower():
                    target_user_id = m.user.id
                    break
            if not target_user_id:
                bot.reply_to(message, f"❌ 找不到用戶 @{target_username}（僅限管理員）")
                return
        except Exception as e:
            bot.reply_to(message, f"❌ 查找用戶時發生錯誤：{e}")
            return
        from datetime import datetime
        today_str = datetime.now().strftime('%m/%d')
        use_date = date_str if date_str else today_str
        # 幣別與類型判斷
        if type_prefix == 'TW+':
            currency = 'TWD'
            action = 'deposit'
        elif type_prefix == 'CN+':
            currency = 'CNY'
            action = 'deposit'
        elif type_prefix == '公桶+':
            currency = 'USDT'
            action = 'public'
        elif type_prefix == '私人+':
            currency = 'USDT'
            action = 'private'
        else:
            bot.reply_to(message, "❌ 不支援的類型")
            return
        # 寫入資料
        config.add_transaction(amount, action, currency=currency, username=target_username, user_id=target_user_id, date=use_date)
        bot.reply_to(message, f"✅ 已幫 @{target_username} 記錄{use_date} {type_prefix}{amount}")
        # 顯示該用戶的最新摘要
        fake_message = type('obj', (object,), {'from_user': type('obj', (object,), {'username': target_username, 'id': target_user_id})})
        bot.reply_to(message, get_transaction_message(fake_message))
    except Exception as e:
        bot.reply_to(message, f"❌ 處理指令時發生錯誤：{str(e)}")

# 處理異動提醒開關
@bot.message_handler(func=lambda m: m.text in ['🔈異動提醒開', '🔇異動提醒關'])
def handle_change_notify_toggle(message):
    global change_notify_enabled, file_change_notify_enabled
    change_notify_enabled = not change_notify_enabled
    file_change_notify_enabled = change_notify_enabled  # 同步檔案異動提醒
    status = '已開啟' if change_notify_enabled else '已關閉'
    btn = '🔈異動提醒開' if change_notify_enabled else '🔇異動提醒關'
    bot.reply_to(message, f'異動提醒{status}', reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: bool(re.match(r"刪除 @\w+ \d{1,2}月分業績總表", message.text or "")))
def handle_delete_user_month_report(message):
    try:
        # 僅限群主
        if not is_group_owner(message.from_user.id, message.chat.id):
            bot.reply_to(message, "❌ 只有群主可以使用此指令")
            return
        match = re.match(r"刪除 @(\w+) (\d{1,2})月分業績總表", message.text)
        if not match:
            bot.reply_to(message, "❌ 格式錯誤，請用：刪除 @用戶名 MM月分業績總表")
            return
        target_username = match.group(1)
        month = match.group(2).zfill(2)
        # 只查管理員
        target_user_id = None
        try:
            admins = bot.get_chat_administrators(message.chat.id)
            for m in admins:
                if m.user.username and m.user.username.lower() == target_username.lower():
                    target_user_id = m.user.id
                    break
            if not target_user_id:
                bot.reply_to(message, f"❌ 找不到用戶 @{target_username}（僅限管理員）")
                return
        except Exception as e:
            bot.reply_to(message, f"❌ 查找用戶時發生錯誤：{e}")
            return
        # 執行刪除（假設 config 有 clear_user_month_report(user_id, month) 方法）
        try:
            if hasattr(config, 'clear_user_month_report'):
                config.clear_user_month_report(target_user_id, month)
                bot.reply_to(message, f'✅ 已刪除 @{target_username} {month}月分業績總表！')
            else:
                bot.reply_to(message, f'（模擬）已刪除 @{target_username} {month}月分業績總表！')
        except Exception as e:
            bot.reply_to(message, f'❌ 刪除時發生錯誤：{e}')
    except Exception as e:
        bot.reply_to(message, f'❌ 指令處理時發生錯誤：{e}')

@bot.callback_query_handler(func=lambda call: call.data == 'main_history')
def main_history_callback(call):
    message = call.message
    if not is_admin(call.from_user.id, message.chat.id):
        bot.answer_callback_query(call.id, '❌ 僅限管理員使用', show_alert=True)
        return
    msg = get_history_message()
    msg += get_current_month_report_message()
    bot.send_message(message.chat.id, msg, reply_markup=create_report_menu())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'main_delete')
def main_delete_callback(call):
    message = call.message
    if not is_admin(call.from_user.id, message.chat.id):
        bot.answer_callback_query(call.id, '❌ 僅限管理員使用', show_alert=True)
        return
    bot.send_message(message.chat.id, '請選擇要刪除的總表：', reply_markup=create_delete_menu())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'main_admin')
def main_admin_callback(call):
    message = call.message
    # 這裡可根據需求顯示權限管理功能
    bot.send_message(message.chat.id, '請選擇權限管理功能（此處可自訂）')
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'main_restart')
def main_restart_callback(call):
    message = call.message
    if not is_admin(call.from_user.id, message.chat.id):
        bot.answer_callback_query(call.id, '❌ 此命令僅限管理員使用', show_alert=True)
        return
    with open('restart.flag', 'w') as f:
        f.write('restart')
    bot.send_message(message.chat.id, '⚠️ 系統即將重新啟動...')
    import os
    os._exit(0)

@bot.callback_query_handler(func=lambda call: call.data == 'main_help')
def main_help_callback(call):
    message = call.message
    guide = (
        '1️⃣TW+999999\n'
        '2️⃣CN+999999\n'
        '3️⃣公桶+300\n'
        '4️⃣私人+300\n'
        '5️⃣設定匯率TW33.33\n'
        '6️⃣設定匯率CN33.33\n'
        '7️⃣重啟\n'
        '⚠️以上指令都有 ± 功能，自行變通。'
    )
    bot.send_message(message.chat.id, guide)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text.strip() == '初始化')
def handle_init_text(message):
    show_main_menu(message) 