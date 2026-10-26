import altair as alt
import pytz
from calendar_fetcher import fetch_economic_events, get_imminent_events, get_next_event
import streamlit as st
import textwrap
import streamlit.components.v1
import os
import json
import time
import requests
from dotenv import load_dotenv
from news_fetcher import fetch_news
from datetime import datetime, timedelta
import email.utils as eut

st.set_page_config(page_title="Lipi Trade AI", page_icon="📈", layout="wide")

# === Custom CSS: Black + Red Theme ===
st.markdown("""
<style>
    /* Making input boxes dark */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #1A1A1A !important;
        color: white !important;
        border: 1px solid #EF4444 !important;
    }
    /* Dark tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1A1A1A;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #E5E7EB;
    }
    .stTabs [aria-selected="true"] {
        background-color: #EF4444 !important;
        color: white !important;
    }
    /* Global Theme */
    .stApp { background-color: #0A0A0A; color: #E5E5E5; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    h1 { color: #EF4444 !important; font-weight: 800 !important; }
    h2, h3 { color: #EF4444 !important; }
    .ticker-container { display: flex; gap: 24px; overflow-x: auto; background: #121212; border: 1px solid #1F1F1F; border-radius: 8px; padding: 12px 20px; margin-bottom: 20px; white-space: nowrap; }
    .ticker-item { display: flex; gap: 8px; font-size: 14px; align-items: center; }
    .ticker-symbol { color: #FFFFFF; font-weight: 600; }
    .ticker-up { color: #22C55E; } .ticker-down { color: #EF4444; }
    .news-card { background: #121212; border: 1px solid #1F1F1F; border-radius: 12px; padding: 18px; margin-bottom: 14px; }
    .news-card:hover { border-color: #EF4444; }
    .news-source { color: #888; font-size: 12px; margin-bottom: 8px; }
    .news-title { color: #FFFFFF; font-size: 18px; font-weight: 600; margin-bottom: 8px; }
    .news-summary { color: #B0B0B0; font-size: 14px; line-height: 1.5; margin-bottom: 10px; }
    .news-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; margin-right: 6px; }
    .badge-bullish { background: rgba(34, 197, 94, 0.15); color: #22C55E; border: 1px solid #22C55E; }
    .badge-bearish { background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid #EF4444; }
    .badge-neutral { background: rgba(150, 150, 150, 0.15); color: #AAA; border: 1px solid #888; }
    .badge-impact { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #EF4444; }
    .breaking { border: 2px solid #EF4444 !important; box-shadow: 0 0 20px rgba(239, 68, 68, 0.4); }
    /* Popover (Profile Menu) Dark Theme */
[data-testid="stPopoverBody"] {
    background-color: #121212 !important;
    color: white !important;
    border: 1px solid #EF4444 !important;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.5) !important;
}
[data-testid="stPopoverBody"] p, [data-testid="stPopoverBody"] div {
    color: white !important;
}
[data-testid="stPopover"] > button {
    background-color: transparent !important;
    border: 1px solid #333 !important;
    color: white !important;
}
[data-testid="stPopover"] > button:hover {
    border: 1px solid #EF4444 !important;
}
</style>
""", unsafe_allow_html=True)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-flash-latest"

from groq import Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "qwen/qwen3.8-27b"

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_summary(title, description, language):
    """Cached AI summary with delay to avoid rate limit."""
    time.sleep(2)
    try:
        result = summarize_news(title, description, language)
        return result
    except Exception as e:
        return {"error": str(e)}

def summarize_news(title, description, language="বাংলা"):
    prompt = f"""You are a financial news analyst. Return ONLY valid JSON.

News Title: {title}
News Description: {description}

Return this structure:
{{
  "summary": "2-sentence summary in {language}",
  "sentiment": "bullish" or "bearish" or "neutral",
  "impact": "high" or "medium" or "low",
  "key_point": "One key takeaway in {language}"
}}
Return ONLY JSON, no markdown.
"""
    for attempt in range(3):
        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            ai_text = response.choices[0].message.content.strip()
            ai_text = ai_text.replace("json", "").replace("", "").strip()
            try:
                return json.loads(ai_text)
            except json.JSONDecodeError:
                return {"error": "AI did not return valid JSON", "raw": ai_text}
        except Exception as e:
            err = str(e)
            if "rate_limit" in err.lower() or "429" in err:
                time.sleep(5)
                continue
            if attempt < 2:
                time.sleep(2)
                continue
            return {"error": f"AI Error: {err[:200]}"}
    return {"error": "Rate limit exceeded. Please wait."}

# === লগইন সিস্টেম সেটআপ ===
import yaml
import streamlit_authenticator as stauth

with open('config.yaml', encoding='utf-8') as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- কাস্টম CSS ডিজাইন ---
st.markdown("""
<style>
    /* মেইন ব্যাকগ্রাউন্ড */
    .stApp { background-color: #0A0A0A; }
    
    /* বাম দিকের প্যানেল ডিজাইন */
    .left-panel {
        background-image: url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=2070&auto=format&fit=crop'); /* ট্রেডিং চার্টের ব্যাকগ্রাউন্ড */
        background-size: cover;
        background-position: center;
        background-color: #000;
        border: 1px solid #2A2A2A;
        border-radius: 12px;
        padding: 40px;
        height: 100%;
        position: relative;
        box-shadow: 0px 0px 30px rgba(239, 68, 68, 0.1);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    /* ইমেজের ওপরে কালো শেড */
    .left-panel::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, rgba(10,10,10,0.9) 0%, rgba(10,10,10,0.6) 100%);
        border-radius: 12px;
        z-index: 1;
    }
    
    /* টেক্সটগুলো যেন শেডের ওপরে থাকে */
    .left-content { position: relative; z-index: 2; }
    
    .logo-text { font-size: 32px; font-weight: 900; color: #FFFFFF; letter-spacing: 1px; }
    .logo-text span { color: #EF4444; }
    .subtitle { color: #AAAAAA; font-size: 16px; margin-bottom: 30px; }
    
    .big-headline { font-size: 48px; font-weight: 800; color: #FFFFFF; line-height: 1.1; margin-bottom: 20px; }
    .big-headline span { color: #EF4444; }
    .desc-text { color: #CCCCCC; font-size: 16px; margin-bottom: 30px; line-height: 1.5; }
    
    /* ফিচার বাটন */
    .feature-btn {
        background-color: rgba(20, 20, 20, 0.8);
        border: 1px solid #333;
        border-left: 4px solid #EF4444;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 15px;
        color: #FFFFFF;
        font-weight: 600;
        font-size: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: 0.3s;
    }
    .feature-btn:hover { background-color: rgba(239, 68, 68, 0.1); border-color: #EF4444; }
    
    /* ডান দিকের লগইন বক্স */
    .right-panel {
        background-color: #111111;
        border: 1px solid #2A2A2A;
        border-radius: 12px;
        padding: 40px;
        height: 100%;
        box-shadow: -10px 0px 30px rgba(0,0,0,0.5);
    }
    
    /* স্ট্রিমলিটের ইনপুট বক্স ও বাটন ডিজাইন */
    .stTextInput>div>div>input {
        background-color: #1A1A1A !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }
    .stTextInput>div>div>input:focus { border: 1px solid #EF4444 !important; box-shadow: 0 0 10px rgba(239,68,68,0.3) !important; }
    
    .stButton>button {
        background: linear-gradient(90deg, #EF4444, #DC2626) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        width: 100% !important;
        font-weight: bold !important;
        padding: 12px 0px !important;
        font-size: 16px !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0px 0px 20px rgba(239, 68, 68, 0.5) !important;
        transform: translateY(-2px);
    }
    
    /* স্ট্রিমলিট ফর্মের সাদা বর্ডার রিমুভ করা */
    [data-testid="stForm"] { border: none !important; padding: 0px !important; }
</style>
""", unsafe_allow_html=True)

import base64

# লোগো ফাইলটি Base64 এ কনভার্ট করা
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

# আমরা যেহেতু logo.jpg বা logo.png দুটোই রাখছি, কোডটি দুটোই চেক করবে
import os
logo_path = "logo.png" if os.path.exists("logo.png") else "logo.jpg"
logo_base64 = get_base64_image(logo_path)

# === লোগো Base64 এ কনভার্ট করার সেটআপ ===
import base64
import os

def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            ext = image_path.split('.')[-1].lower()
            mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""

# যেই ফাইলটা আগে পাবে সেটাই নেবে (logo.png বা logo.jpg)
logo_path = "logo.png" if os.path.exists("logo.png") else "logo.jpg"
logo_base64 = get_base64_image(logo_path)

if logo_base64:
    img_tag = f'<img src="{logo_base64}" style="width: 60px; height: 60px; margin-right: 15px; border-radius: 12px;" />'
else:
    img_tag = '<span style="font-size: 40px; margin-right: 15px;">📈</span>'

# যদি ইউজার লগইন না করে থাকে
if st.session_state.get("authentication_status") is not True:
    
    col1, col2 = st.columns([1.3, 1], gap="large")
    
    with col1:
        # খেয়াল করুন: বড় হাতের F দেওয়া হয়েছে, এবং HTML ট্যাগগুলো একদম বামে
        left_html = f"""<div class="left-panel">
<div class="left-content">
<div style="display: flex; align-items: center; margin-bottom: 10px;">
{img_tag}
<div>
<div class="logo-text">LIPI <span>TRADE AI</span></div>
<div class="subtitle" style="margin-bottom: 0;">Your Digital Trading Workspace</div>
</div>
</div>
<div style="margin-top: 50px;">
<div class="big-headline">The News That<br><span>Moves Markets</span></div>
<div class="desc-text">Get real-time financial news, AI-powered summaries, breaking news alerts, and the latest market insights — all in one place.</div>
</div>
<div style="margin-top: 40px;">
<div class="feature-btn"><span>📈 Live Market Prices</span> <span>→</span></div>
<div class="feature-btn"><span>🤖 AI-Powered News Summaries</span> <span>→</span></div>
<div class="feature-btn"><span>🔔 Breaking News Alerts</span> <span>→</span></div>
<div class="feature-btn"><span>📅 Real-time Economic Calendar</span> <span>→</span></div>
<div class="feature-btn"><span>📸 AI Screenshot Analyzer</span> <span>→</span></div>
</div>
</div>
</div>"""
        st.markdown(left_html, unsafe_allow_html=True)
        
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: white; margin-bottom: 0px;'>AI-Powered News Intelligence 🤖</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #888; font-size: 14px; margin-bottom: 20px;'>Log in to access your dashboard, manage your account, and continue securely with full control.</p>", unsafe_allow_html=True)
        
        authenticator.login(location='main')
        
        if st.session_state["authentication_status"] is False:
            st.error('❌ ইউজারনেম বা পাসওয়ার্ড ভুল হয়েছে!')
    
    st.markdown(
        "<div style='text-align: center; color: #555; font-size: 12px; margin-top: 50px;'>Built by Niloy 💙 | Lipi Trade AI v0.2</div>", 
        unsafe_allow_html=True
    )
    
    st.stop()

# === এখান থেকে আপনার আগের সব কোড (Header, Ticker, Tabs) চলবে ===
# (লগআউট বাটনের কোড ইত্যাদি)

# === লগইন সফল হলে (মেইন অ্যাপ শুরু) ===

# মেইন পেজের একদম উপরে ডানদিকে প্রোফাইল মেনু
st.markdown("<br>", unsafe_allow_html=True) # একটু ফাঁকা জায়গা
top_space, top_profile = st.columns([8.5, 1.5])

with top_profile:
    # পপওভার মেনু (ক্লিক করলে ড্রপডাউন খুলবে)
    with st.popover(f"👤 {st.session_state.get('name')} ▼"):
        st.markdown(f"*{st.session_state.get('name')}*")
        st.markdown(f"{st.session_state.get('username')}")
        st.divider()
        # লগআউট বাটন
        authenticator.logout("🚪 Logout", "main")

st.divider() # একটি সুন্দর হরাইজন্টাল লাইন

# === Header ===
st.markdown("# 📈 Lipi Trade AI")
# ... (এখান থেকে আপনার আগের সব কোড চলবে) ...
st.markdown("##### Real-time Multi-Language Trading Intelligence")
st.markdown("---")

import yfinance as yf
import textwrap
# === Telegram Alert Function ===
def send_telegram_alert(message):
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if bot_token and chat_id:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

# === Header === (এটি আপনার আগের কোডেই আছে)
@st.fragment(run_every=10)
def render_live_ticker():
    symbols = {
        "BTC-USD": "BTCUSD",
        "GC=F": "XAUUSD", 
        "CL=F": "WTI",
        "EURUSD=X": "EURUSD",
        "AAPL": "AAPL"
    }
    tickers = []
    try:
        tickers_data = yf.Tickers(" ".join(symbols.keys()))
        for yf_symbol, display_symbol in symbols.items():
            t = tickers_data.tickers[yf_symbol].fast_info
            price = t.last_price
            prev_close = t.previous_close
            if price and prev_close:
                change = price - prev_close
                pct = (change / prev_close) * 100
                tickers.append({
                    "symbol": display_symbol,
                    "price": f"{price:,.2f}",
                    "change": f"{pct:+.2f}%",
                    "up": change >= 0
                })
    except Exception as e:
        # Fallback to mock if Yahoo Finance fails
        tickers = [
            {"symbol": "BTCUSD", "price": "67,420.50", "change": "+1.23%", "up": True},
            {"symbol": "XAUUSD", "price": "2,385.20", "change": "-0.27%", "up": False},
        ]

    if tickers:
        ticker_html = '<div class="ticker-container">'
        for t in tickers:
            arrow = "▲" if t["up"] else "▼"
            cls = "ticker-up" if t["up"] else "ticker-down"
            ticker_html += f'<div class="ticker-item"><span class="ticker-symbol">{t["symbol"]}</span><span>{t["price"]}</span><span class="{cls}">{arrow} {t["change"]}</span></div>'
        ticker_html += '</div>'
        st.markdown(textwrap.dedent(ticker_html).replace("\n", ""), unsafe_allow_html=True)

render_live_ticker()

# Create Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📰 Market News & Calendar", "🧮 Trading Tools", "📈 Performance & Alerts", "💬 AI Chatbot"])

# ==========================================
# TAB 1: MARKET NEWS & CALENDAR
# ==========================================
with tab1:
    # === Event Alert System (Real Data & Refactored) ===
    bd_tz = pytz.timezone("Asia/Dhaka")
    now_bd = datetime.now(bd_tz)

    imminent = get_imminent_events(minutes=30)

    if imminent:
        if 'shown_alerts' not in st.session_state:
            st.session_state.shown_alerts = set()
            
        for ev in imminent:
            alert_key = f"{ev.get('country', '')}-{ev.get('title', '')}"
            if alert_key not in st.session_state.shown_alerts:
                st.error(
                    f"*{ev.get('country', '')} {ev.get('title', '')}* in {ev.get('mins', '?')} minutes!\n"
                    f"Forecast: {ev.get('forecast', 'N/A')} | "
                    f"High volatility expected – prepare your positions.",
                    icon="🚨"
                )
                st.session_state.shown_alerts.add(alert_key)
                # টেলিগ্রামে ইভেন্ট অ্যালার্ট পাঠানো
        alert_msg = (
            f"⚠️ *UPCOMING EVENT!*\n"
            f"{ev.get('country', '')} {ev.get('title', '')} in {ev.get('mins', '?')} minutes!\n"
            f"Forecast: {ev.get('forecast', 'N/A')}"
        )
        send_telegram_alert(alert_msg)

    else:
        next_ev = get_next_event()
        if next_ev:
            diff = (next_ev["datetime_bd"] - datetime.now(bd_tz)).total_seconds() / 60
            hours = int(diff // 60)
            mins = int(diff % 60)
            time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            
            st.markdown(
                f"""
                <div style="background-color: #0A0A0A; border-left: 4px solid #3B82F6; padding: 10px; border-radius: 5px; color: #9CA3AF;">
                    📅 Market Calm. Next High Impact: <b>{next_ev.get('country', '')} {next_ev.get('title', '')}</b> in <b>{time_str}</b>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="background-color: #0A0A0A; border-left: 4px solid #6B7280; padding: 10px; border-radius: 5px; color: #9CA3AF;">
                    📅 No upcoming events this week.
                </div>
                """, 
                unsafe_allow_html=True
            )

    # === Breaking News Alert ===
    try:
        _breaking_news = fetch_news("Crypto", limit=3)
        _high_impact = []
        _keywords = ["breaking", "emergency", "crash", "plunge", "surge", "hack", "ban", "fed", "fomc", "cpi", "crypto"]
        
        for _bn in _breaking_news[:3]:
            _text = (_bn.get("title", "") + " " + _bn.get("description", "")).lower()
            if any(k in _text for k in _keywords):
                _high_impact.append(_bn)
        
        if _high_impact:
            st.markdown("## 🚨 Breaking News Alerts")
            for _b in _high_impact[:2]:
                st.error(
                    f"{_b['source']} — {_b['title'][:120]}\n\n"
                    f"🔗 [Read full article]({_b['link']})",
                    icon="🔥"
                )
    except Exception:
        pass

    # === Two Columns Layout (News & Calendar) ===
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("## 📰 Market News")
        col_lang, col_cat = st.columns(2)
        with col_lang:
            news_lang_label = st.selectbox(
                "🌐 Language",
                ["English", "বাংলা", "हिंदी", "اردو", "日本語", "Bahasa Melayu"],
                index=0,
                key="news_lang_select"
            )
        with col_cat:
            news_category = st.selectbox(
                "📂 Category",
                ["Crypto", "Stocks", "Forex", "Global"],
                index=0,
                key="news_category_select"
            )

        with st.spinner(f"Loading {news_category} news..."):
            real_news = fetch_news(news_category, limit=5)

        if real_news:
            lang_map = {
                "English": "English",
                "বাংলা": "বাংলা",
                "हिंदी": "हिंदी",
                "اردو": "اردو",
                "日本語": "日本語",
                "Bahasa Melayu": "Bahasa Melayu",
            }
            ai_lang = lang_map.get(news_lang_label, "English")

            for article in real_news[:3]:
                with st.container(border=True):
                    st.markdown(f"{article['source']}")
                    st.markdown(f"### {article['title']}")

                    published_time = article.get('published', '')
                    if published_time:
                        try:
                            dt = eut.parsedate_to_datetime(published_time)
                            formatted = dt.strftime("%d %b, %I:%M %p")
                            now = datetime.now(dt.tzinfo)
                            diff = now - dt

                            ago_words = {
                                "English": ("minutes ago", "hours ago", "days ago"),
                                "বাংলা": ("মিনিট আগে", "ঘণ্টা আগে", "দিন আগে"),
                                "हिंदी": ("मिनट पहले", "घंटे पहले", "दिन पहले"),
                                "اردو": ("منٹ پہلے", "گھنٹے پہلے", "دن پہلے"),
                                "日本語": ("分前", "時間前", "日前"),
                                "Bahasa Melayu": ("minit lalu", "jam lalu", "hari lalu"),
                            }
                            min_word, hour_word, day_word = ago_words.get(ai_lang, ago_words["English"])

                            if diff.days == 0:
                                hours = diff.seconds // 3600
                                if hours < 1:
                                    ago = f"{diff.seconds // 60} {min_word}"
                                else:
                                    ago = f"{hours} {hour_word}"
                            else:
                                ago = f"{diff.days} {day_word}"

                            st.caption(f"🕐 {formatted} • {ago}")
                        except Exception:
                            st.caption(f"🕐 {published_time[:25]}")

                    with st.spinner(f"🤖 AI summarizing in {ai_lang}..."):
                        ai_result = get_cached_summary(article['title'], article['description'], ai_lang)

                    if "error" not in ai_result:
                        st.info(f"📝 AI Summary: {ai_result.get('summary', '')}")
                        sc1, sc2 = st.columns(2)
                        sentiment = ai_result.get('sentiment', 'neutral').upper()
                        impact = ai_result.get('impact', 'low').upper()

                        if sentiment == "BULLISH":
                            sc1.success(f"📈 {sentiment}")
                        elif sentiment == "BEARISH":
                            sc1.error(f"📉 {sentiment}")
                        else:
                            sc1.warning(f"➖ {sentiment}")

                        sc2.metric("Impact", impact)
                    else:
                        st.caption("AI summary unavailable")

                    st.caption(f"🔗 [Read full article]({article['link']})")  

    with col2:
        st.markdown("## 📅 Economic Calendar")
        all_events = fetch_economic_events()
        now_bd = datetime.now(bd_tz)

        upcoming = [e for e in all_events if e["datetime_bd"] > now_bd][:8]

        if upcoming:
            for e in upcoming:
                dt = e["datetime_bd"]
                time_str = dt.strftime("%a %d %b, %I:%M %p")

                if e["impact"] == "HIGH":
                    border = "border-left: 4px solid #EF4444;"
                elif e["impact"] == "MEDIUM":
                    border = "border-left: 4px solid #F59E0B;"
                else:
                    border = "border-left: 4px solid #444;"

                forecast = e.get("forecast", "") or "-"

                cal_html = f'''<div style="background:#121212; {border} border-radius:8px; padding:10px; margin-bottom: 10px; color: white;">
                    <span style="font-size: 14px; font-weight: bold;">{e.get("country", "")} {e.get("title", "")}</span><br>
                    <span style="font-size: 12px; color: #aaa;">⏰ {time_str} | Forecast: {forecast}</span>
                </div>'''
                st.markdown(textwrap.dedent(cal_html).replace("\n", ""), unsafe_allow_html=True)
        else:
            st.info("No upcoming events this week.")


# ==========================================
# TAB 2: TRADING TOOLS
# ==========================================
with tab2:
    # === Risk-Reward Calculator ===
    st.markdown("## 🎯 Risk-Reward Calculator")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        entry = st.number_input("Entry Price", value=0.0, step=0.01)
        account_balance = st.number_input("Account Balance ($)", value=1000.0, step=10.0)
    with col_b:
        stop_loss = st.number_input("Stop Loss", value=0.0, step=0.01)
        risk_percent = st.number_input("Risk %", value=2.0, step=0.1)
    with col_c:
        take_profit = st.number_input("Take Profit", value=0.0, step=0.01)

    if entry > 0 and stop_loss > 0 and take_profit > 0:
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        rr = reward / risk if risk > 0 else 0
        risk_amount = account_balance * (risk_percent / 100)
        position_size = risk_amount / risk if risk > 0 else 0

        st.divider()
        st.markdown("### 📊 Results")
        res1, res2, res3 = st.columns(3)
        res1.metric("Risk (per unit)", f"{risk:.2f}")
        res2.metric("Reward (per unit)", f"{reward:.2f}")
        res3.metric("Risk-Reward Ratio", f"1 : {rr:.2f}")

        res4, res5 = st.columns(2)
        res4.metric("💰 Risk Amount", f"${risk_amount:.2f}")
        res5.metric("📈 Position Size", f"{position_size:.2f} units")

        if rr >= 2:
            st.success(f"✅ Good setup! RR = 1:{rr:.2f} (target ≥ 1:2) - You can take it")
            st.balloons()
        elif rr >= 1:
            st.warning(f"⚠️ Borderline. RR = 1:{rr:.2f} - Think before entering")
        else:
            st.error(f"❌ Bad setup! RR = 1:{rr:.2f} — Do not take this trade")

    st.markdown("---")
    
    # === AI News Summarizer ===
    st.markdown("## 📰 AI News Summarizer")
    st.caption("Enter the news Title and Description — AI will generate a summary in your chosen language.")
    LANG_OPTIONS = {
        "বাংলা (Bengali)": "বাংলা",
        "English": "English",
        "हिंदी (Hindi)": "हिंदी",
        "اردو (Urdu)": "اردو",
        "日本語 (Japanese)": "日本語",
        "Bahasa Melayu (Malay)": "Bahasa Melayu",
    }
    selected_lang_label = st.selectbox("🌐 Summary Language", list(LANG_OPTIONS.keys()), key="ai_news_lang")
    selected_lang = LANG_OPTIONS[selected_lang_label]
    ai_news_title = st.text_input("News Title", key="ai_news_title_input")
    ai_news_desc = st.text_area("News Description", key="ai_news_desc_input")

    if st.button("🤖 Summarize with AI", key="summarize_btn"):
        if not ai_news_title.strip():
            st.warning("⚠️ Please enter a news title!")
        else:
            with st.spinner(f"AI Analyzing in {selected_lang}... please wait"):
                result = summarize_news(ai_news_title, ai_news_desc, selected_lang)
                if "error" not in result:
                    st.success(result.get("summary", ""))
                    col1, col2 = st.columns(2)
                    col1.metric("Sentiment", result.get("sentiment", "N/A").upper())
                    col2.metric("Impact", result.get("impact", "N/A").upper())
                    st.info(f"💡 Key Point: {result.get('key_point', 'N/A')}")
                else:
                    st.error(f"❌ Error: {result.get('error')}")

    st.markdown("---")

    # === Trade Screenshot Analyzer ===
    st.markdown("## 📸 AI Trade Screenshot Analyzer")
    st.caption("Upload your trade chart screenshot — AI will analyze and give you feedback.")
    from trade_analyzer import analyze_trade_screenshot

    col_a, col_b = st.columns([1, 1])
    with col_a:
        uploaded_file = st.file_uploader("Upload Trade Screenshot", type=["png", "jpg", "jpeg", "webp"], key="trade_screenshot")
    with col_b:
        trade_notes = st.text_area("Notes (optional)", placeholder="e.g., EURUSD 5-min chart, London session...", key="trade_notes", height=120)

    TA_LANG_OPTIONS = {
        "বাংলা (Bengali)": "বাংলা",
        "English": "English",
        "हिंदी (Hindi)": "हिंदी",
        "اردو (Urdu)": "اردو",
        "日本語 (Japanese)": "日本語",
        "Bahasa Melayu (Malay)": "Bahasa Melayu",
    }
    ta_lang_label = st.selectbox("🌐 Analysis Language", list(TA_LANG_OPTIONS.keys()), key="ta_lang")
    ta_lang = TA_LANG_OPTIONS[ta_lang_label]

    if st.button("🔍 Analyze Trade", key="analyze_trade_btn"):
        if uploaded_file is None:
            st.warning("⚠️ Please upload a screenshot first!")
        else:
            with st.spinner(f"AI analyzing in {ta_lang}... this may take 15-30 seconds"):
                image_bytes = uploaded_file.read()
                result = analyze_trade_screenshot(image_bytes, trade_notes, ta_lang)

                if "error" not in result:
                    rating = result.get("overall_rating", "unknown").upper()
                    if rating in ["EXCELLENT", "GOOD"]:
                        st.success(f"✅ Overall Rating: {rating}")
                    elif rating == "AVERAGE":
                        st.warning(f"⚠️ Overall Rating: {rating}")
                    else:
                        st.error(f"❌ Overall Rating: {rating}")

                    col1, col2 = st.columns(2)
                    col1.metric("Risk-Reward Estimate", result.get("rr_estimate", "unknown"))
                    col2.metric("Confidence", f"{result.get('confidence', 0)*100:.0f}%")

                    st.markdown("### ❌ Mistakes")
                    for m in result.get("mistakes", []):
                        st.markdown(f"- {m}")

                    st.markdown("### 💡 Suggestions")
                    for s in result.get("suggestions", []):
                        st.markdown(f"- {s}")
                else:
                    st.error(f"❌ Error: {result.get('error')}")


# ==========================================
# TAB 3: PERFORMANCE & ALERTS
# ==========================================
with tab3:
    # === Performance Dashboard ===
    st.markdown("## 📊 Performance Dashboard")
    st.caption("Log your trades and track your win rate, RR, drawdown, and equity curve.")
    from performance import load_trades, add_trade, calculate_metrics

    with st.expander("➕ Add a New Trade", expanded=False):
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            p_symbol = st.text_input("Symbol", key="p_symbol", placeholder="BTCUSD")
            p_side = st.selectbox("Side", ["Buy", "Sell"], key="p_side")
        with pc2:
            p_entry = st.number_input("Entry Price", value=0.0, step=0.01, key="p_entry")
            p_exit = st.number_input("Exit Price", value=0.0, step=0.01, key="p_exit")
        with pc3:
            p_sl = st.number_input("Stop Loss", value=0.0, step=0.01, key="p_sl")
            p_tp = st.number_input("Take Profit", value=0.0, step=0.01, key="p_tp")
        p_pnl = st.number_input("Profit / Loss ($)", value=0.0, step=0.01, key="p_pnl")
        p_notes = st.text_input("Notes (optional)", key="p_notes")

        if st.button("💾 Save Trade", key="save_trade_btn"):
            if p_symbol.strip() and p_entry > 0:
                add_trade(p_symbol, p_side, p_entry, p_exit, p_sl, p_tp, p_pnl, p_notes)
                st.success(f"✅ Trade saved: {p_symbol} {p_side}")
                st.rerun()
            else:
                st.warning("⚠️ Please enter Symbol and Entry Price")

    trades = load_trades()
    metrics = calculate_metrics(trades)

    if metrics["trade_count"] > 0:
        st.markdown("### 📈 Your Performance")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Trades", metrics["trade_count"])
        m2.metric("Win Rate", f"{metrics['win_rate']}%")
        m3.metric("Avg RR", f"1:{metrics['avg_rr']}")
        m4.metric("Max Drawdown", f"{metrics['max_drawdown']}%")

        m5, m6 = st.columns(2)
        m5.metric("Total P&L", f"${metrics['total_pnl']}")
        if metrics["equity_curve"]:
            m6.metric("Current Equity", f"${metrics['equity_curve'][-1]['equity']}")

        if metrics["equity_curve"]:
            import pandas as pd
            df = pd.DataFrame(metrics["equity_curve"])
            st.markdown("### 📉 Equity Curve")
            chart = alt.Chart(df).mark_line(color="#EF4444").encode(
                x="trade:O",
                y="equity:Q"
            ).properties(background="#0A0A0A")
            st.altair_chart(chart, use_container_width=True)
            
        st.markdown("### 📋 Trade History")
        for t in reversed(trades):
            if t["pnl"] > 0:
                color = "🟢"
            elif t["pnl"] < 0:
                color = "🔴"
            else:
                color = "⚪"
            st.markdown(
                f"{color} {t['symbol']} {t['side']} | "
                f"Entry: {t['entry']} | Exit: {t['exit']} | "
                f"P&L: ${t['pnl']} | {t['date']}"
            )
    else:
        st.info("📭 No trades yet. Add your first trade above to see your performance metrics.")

    st.markdown("---")

    # === Price Alert System ===
    st.markdown("## 🔔 Price Alert System")
    st.caption("Set price alerts for BTC, Gold, Oil, and get notified when price hits your target.")
    from alerts import load_alerts, add_alert, delete_alert, check_alerts

    with st.expander("➕ Add New Alert", expanded=False):
        pa1, pa2, pa3 = st.columns(3)
        with pa1:
            alert_symbol = st.selectbox("Symbol", ["BTCUSD", "XAUUSD", "WTI", "EURUSD", "AAPL"], key="alert_symbol")
        with pa2:
            alert_target = st.number_input("Target Price", value=0.0, step=0.01, key="alert_target")
        with pa3:
            alert_condition = st.selectbox("When price goes", ["above", "below"], key="alert_condition")
        
        alert_note = st.text_input("Note (optional)", key="alert_note")
        
        if st.button("💾 Save Alert", key="save_alert_btn"):
            if alert_target > 0:
                add_alert(alert_symbol, alert_target, alert_condition, alert_note)
                st.success(f"✅ Alert saved: {alert_symbol} {alert_condition} {alert_target}")
                st.rerun()
            else:
                st.warning("⚠️ Please enter a target price")

    # --- Check Triggered Alerts (Live Prices) ---

# ১ মিনিটের জন্য ডেটা ক্যাশ করে রাখা, যাতে ইয়াহু ফাইন্যান্স বারবার ডেটা না চায়
@st.cache_data(ttl=60, show_spinner=False)
def get_live_prices():
    prices = {
        "BTCUSD": 67420.50, "XAUUSD": 2385.20, "WTI": 78.90, "EURUSD": 1.0870, "AAPL": 227.40
    }
    try:
        alert_symbols = {
            "BTC-USD": "BTCUSD", "GC=F": "XAUUSD", "CL=F": "WTI", "EURUSD=X": "EURUSD", "AAPL": "AAPL"
        }
        tickers_data = yf.Tickers(" ".join(alert_symbols.keys()))
        for yf_sym, disp_sym in alert_symbols.items():
            live_price = tickers_data.tickers[yf_sym].fast_info.last_price
            if live_price:
                prices[disp_sym] = live_price
    except Exception:
        pass
    return prices

# ফাংশন থেকে দাম নিয়ে আসা
current_prices = get_live_prices()

# ৩. অ্যালার্ট চেক করা
triggered = check_alerts(current_prices)

if triggered:
    for t in triggered:
        st.error(f"🚨 *ALERT HIT!* {t['symbol']} is now *{t['current']:.2f}* ({t['condition']} {t['target']})")
        # টেলিগ্রামে মেসেজ পাঠানো
        send_telegram_alert(f"🚨 *PRICE ALERT HIT!*\n{t['symbol']} is now {t['current']:.2f}\nCondition: {t['condition']} {t['target']}")

# --- Active Alerts List ---
all_alerts = load_alerts()
if all_alerts:
    st.markdown("### 📋 Active Alerts")
    for alert in all_alerts:
        col_a, col_b = st.columns([4, 1])
        with col_a:
            icon = "🟢" if alert.get("active") else "⚪"
            arrow = "🔺" if alert["condition"] == "above" else "🔻"
            st.markdown(f"{icon} {arrow} *{alert['symbol']}* → {alert['condition']} *{alert['target']}* {alert.get('note','')}")
        with col_b:
            if st.button("🗑️", key=f"del_{alert['id']}"):
                delete_alert(alert["id"])
                st.rerun()
else:
    st.info("📭 No alerts yet. Add your first alert above.")


# ==========================================
# TAB 4: AI CHATBOT
# ==========================================
with tab4:
    st.markdown("## 💬 AI Trading Chatbot")
    st.caption("Ask trading-related questions and get insights from the AI.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Your Question:", key="chat_input")
    
    if st.button("Send", key="send_chat_btn"):
        if user_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner("AI is thinking..."):
                try:
                    response = groq_client.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=st.session_state.chat_history,
                        temperature=0.5,
                        max_tokens=500
                    )
                    ai_reply = response.choices[0].message.content.strip()
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"*You:* {msg['content']}")
        else:
            st.markdown(f"*AI:* {msg['content']}")

    if st.button("🗑️ Clear Chat", key="clear_chat_btn"):
        st.session_state.chat_history = []
        st.rerun()

# === Footer ===
st.markdown('<p style="text-align:center; color:#555; font-size:12px;">Built by Niloy 💙 | Lipi Trade AI v0.2</p>', unsafe_allow_html=True)