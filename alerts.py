import json
import os
from datetime import datetime

ALERTS_FILE = "alerts.json"


def load_alerts():
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_alerts(alerts):
    with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)


def add_alert(symbol, target_price, condition, note=""):
    """
    condition: 'above' or 'below'
    """
    alerts = load_alerts()
    alert = {
        "id": len(alerts) + 1,
        "symbol": symbol.upper(),
        "target": float(target_price),
        "condition": condition,
        "note": note,
        "active": True,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    alerts.append(alert)
    save_alerts(alerts)
    return alert


def delete_alert(alert_id):
    alerts = load_alerts()
    alerts = [a for a in alerts if a["id"] != alert_id]
    save_alerts(alerts)


def check_alerts(current_prices):
    """
    current_prices: dict like {"BTCUSD": 67420.50, "XAUUSD": 2385.20}
    Returns list of triggered alerts
    """
    alerts = load_alerts()
    triggered = []

    for alert in alerts:
        if not alert.get("active", True):
            continue

        symbol = alert["symbol"]
        target = alert["target"]
        condition = alert["condition"]

        if symbol not in current_prices:
            continue

        current = current_prices[symbol]

        if condition == "above" and current >= target:
            triggered.append({**alert, "current": current})
        elif condition == "below" and current <= target:
            triggered.append({**alert, "current": current})

    return triggered