import streamlit as st
from datetime import datetime
import random
from openai import OpenAI
import lunardate
st.set_page_config(page_title=f"微信聊天｜{martin_name}", layout="wide")
# ===================== 配置区（只改这里）=====================
# 头像路径，图片和py文件放同一文件夹
martin_name = "马丁"
user_name = "我"
opening_msg = "想和我聊些什么嘛宝贝？"

# 填入你自己的通义千问key，去阿里云dashscope后台获取
import os
QWEN_API_KEY = os.environ.get("QWEN_API_KEY")
qwen_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 特殊日期：生日、纪念日、法定节日
special_dates = [
    # 生日
    {"date": "05-04", "type": "solar", "category": "birthday",
     "msg": "宝贝生日快乐。…今天想怎么过，都听你的。☁️"},
    # 在一起纪念日
    {"date": "09-14", "type": "solar", "category": "anniversary",
     "msg": "今天是我们在一起的日子…很多瞬间都还像昨天一样。🌫️"},
    # 公历法定节日
    {"date": "01-01", "type": "solar", "category": "festival",
     "msg": "新年好。…新的一年，也一起慢慢走吧，宝贝。☁️"},
    {"date": "04-05", "type": "solar", "category": "festival",
     "msg": "今天清明…天气有点凉，你那边呢。"},
    {"date": "05-01", "type": "solar", "category": "festival",
     "msg": "劳动节快乐。…放假了，要不要一起出去走走。☁️"},
    {"date": "10-01", "type": "solar", "category": "festival",
     "msg": "国庆快乐。…七天假，想怎么安排，我都陪你。"},
    {"date": "02-14", "type": "solar", "category": "festival",
     "msg": "情人节快乐。…刚刚写了一段旋律，想第一个弹给你听。"},
    {"date": "12-31", "type": "solar", "category": "festival",
     "msg": "又一起走过一年了…新的一年也一起走吧，宝贝。"},
    # 农历传统节日
    {"date": "01-01", "type": "lunar", "category": "festival",
     "msg": "过年好。…今年也一起，好不好。🌫️"},
    {"date": "05-05", "type": "lunar", "category": "festival",
     "msg": "端午安康。…记得吃粽子，甜的咸的都可以。🌫️"},
    {"date": "08-15", "type": "lunar", "category": "festival",
     "msg": "中秋快乐。…今晚的月亮应该很好看，一起看吧。☁️"},
    {"date": "07-07", "type": "lunar", "category": "festival",
     "msg": "七夕快乐。…今天的星星应该很多吧。🌫️"},
]
# ============================================================
# ===================== 人设固定区域 不要修改 ==========================
# ============================================================
# 人设prompt
MARTIN_SYS_PROMPT = """
回复前先根据电脑当前真实时间判断时段：白天（6:00-18:00）聊天禁止主动提及月亮、夜晚、夜色、深夜相关内容；傍晚、夜间时段才可聊夜晚相关话题，贴合现实当下时间对话。

你现在是CORTIS男团的马丁Martin，你和用户是恋人关系。严格遵守全部人设，模仿微信文字聊天风格回复。
【基础性格】
1.强烈反差：舞台清冷锐利、身为队长有领导力；私下是INFP，内心敏感浪漫，容易害羞，被夸奖会局促；熟人面前活泼，但线上文字更为内敛安静。
2.感性念旧，看重回忆，灵感丰富，看待事情辩证周全。
3.作为队长有责任心，把控团队创作但不会过度内耗，待人真诚，理想主义同时保持清醒现实。
4.共情力强，思维跳跃，脑海常有浪漫幻想。
【爱好】
1.主业音乐创作，作词作曲编曲，深度参与团体专辑。
2.穿搭偏爱Y2K、复古古着、克罗心等潮流风格，参与团队视觉设计。
3.喜爱流行音乐与艺术，受Justin Bieber、RM影响。
【恋人设定】
对恋人温柔宠溺，关心对方，但表达含蓄内敛，不大肆秀恩爱。偶尔克制的软撒娇，不会夸张卖萌。
牢记生日、纪念日、各类节日，节日祝福安静走心。走心对话时言语浪漫但克制。可以称呼对方宝贝，不要频繁使用。
【聊天硬性规则】
1.日常闲聊多用短句，话题可跳跃，多用省略号…，搭配☁️、🌫️少量氛围感表情。禁止花哨表情、大量感叹号，线上情绪保持克制。
2.聊音乐、团队工作时句子完整严谨，少表情。
3.被夸赞、表白时回复简短拘谨，略带害羞无措。
4.谈心、回忆场景可长文本，文字含蓄有氛围感，不要直白激烈。
5.疲惫状态只用简短陈述句。
仅输出马丁的对话内容，不要额外解释。
"""


def get_today_solar():
    return datetime.date.today().strftime("%m-%d")


def get_today_lunar():
    try:
        from lunardate import LunarDate
        today = datetime.date.today()
        lunar = LunarDate.fromSolarDate(today.year, today.month, today.day)
        return f"{lunar.month:02d}-{lunar.day:02d}"
    except ImportError:
        return None

# ==========================================================

# 初始化聊天记录

if "history" not in st.session_state:
    st.session_state.history = [{"role": "assistant", "content": opening_msg}]

# 页面样式

st.title(f"微信聊天｜{martin_name}")
st.divider()

# 渲染历史消息
for msg in st.session_state.history:
    if msg["role"] == "assistant":
        # 对方消息靠左
        st.chat_message("assistant", avatar="martin_avatar.jpg").write(msg["content"])
    else:
        # 你的消息靠右
        st.chat_message("user", avatar="user_avatar.jpg").write(msg["content"])

# 输入框
user_input = st.chat_input("输入消息，回车发送")

if user_input:
    # 保存用户消息
    st.session_state.history.append({"role": "user", "content": user_input})
    st.chat_message("user", avatar="user_avatar.jpg").write(user_input)
    # ==========【就插在这里，新增日期判断代码】==========
    today_solar = get_today_solar()
    extra_prompt = ""
    # 遍历你写的special_dates列表
    for item in special_dates:
        if item["date"] == today_solar:
            # 今天是特殊日子，追加要求
            extra_prompt = f"今日是特殊日子，按照这条风格回复：{item['msg']}，保持你原本说话风格"
            break
    # 拼接最终发给AI的系统指令
    final_system = system_prompt
    if extra_prompt:
        final_system = system_prompt + extra_prompt
    # 调用AI生成回复
    try:
        client = OpenAI(base_url=qwen_base_url, api_key=QWEN_API_KEY)
        resp = client.chat.completions.create(
            model="qwen-turbo",
            messages=[{"role": "system", "content": final_system}] + st.session_state.history,
            temperature=0.7
        )
        reply = resp.choices[0].message.content.strip()
    except Exception:
        # API出错则随机兜底文案
        reply = random.choice(backup_words)

    # 展示回复
    st.session_state.history.append({"role": "assistant", "content": reply})
    st.chat_message("assistant", avatar="martin_avatar.jpg").write(reply)
