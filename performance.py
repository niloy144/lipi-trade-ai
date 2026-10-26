import json
import os
from datetime import datetime

TRADES_FILE = "trades.json"


def load_trades():
    if os.path.exists(TRADES_FILE):
        try:
            with open(TRADES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_trades(trades):
    with open(TRADES_FILE, 'w', encoding='utf-8') as f:
        json.dump(trades, f, ensure_ascii=False, indent=2)


def add_trade(symbol, side, entry, exit_price, stop_loss, take_profit, pnl, notes=""):
    trades = load_trades()
    trade = {
        "id": len(trades) + 1,
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "exit": exit_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "pnl": pnl,
        "notes": notes,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    trades.append(trade)
    save_trades(trades)
    return trade


def calculate_metrics(trades):
    empty = {
        "win_rate": 0, "avg_rr": 0, "max_drawdown": 0,
        "total_pnl": 0, "trade_count": 0, "equity_curve": []
    }
    if not trades:
        return empty

    closed = [t for t in trades if t.get("pnl") is not None]
    if not closed:
        return empty

    # Win rate
    wins = [t for t in closed if t["pnl"] > 0]
    win_rate = (len(wins) / len(closed)) * 100

    # Average RR
    rrs = []
    for t in closed:
        if t.get("stop_loss") and t.get("entry") and t.get("take_profit"):
            risk = abs(t["entry"] - t["stop_loss"])
            reward = abs(t["take_profit"] - t["entry"])
            if risk > 0:
                rrs.append(reward / risk)
    avg_rr = sum(rrs) / len(rrs) if rrs else 0

    # Equity curve + drawdown
    equity = 0
    peak = 0
    max_dd = 0
    equity_curve = []
    for t in closed:
        equity += t["pnl"]
        peak = max(peak, equity)
        dd = ((peak - equity) / peak * 100) if peak > 0 else 0
        max_dd = max(max_dd, dd)
        equity_curve.append({
            "trade": t["id"],
            "equity": round(equity, 2),
        })

    return {
        "win_rate": round(win_rate, 2),
        "avg_rr": round(avg_rr, 2),
        "max_drawdown": round(max_dd, 2),
        "total_pnl": round(sum(t["pnl"] for t in closed), 2),
        "trade_count": len(closed),
        "equity_curve": equity_curve,
    }