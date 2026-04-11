import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime
import pytz

ET = pytz.timezone("America/New_York")

_log_buffer: list[str] = []
_discord_lines: list[str] = []
_current_balance: float = 0.0


def _now() -> str:
    return datetime.now(ET).strftime("%H:%M:%S")


def _today() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d")


def log(msg: str):
    print(f"[{_now()}] {msg}", flush=True)


def _buffer(line: str):
    _log_buffer.append(line)


def _write_obsidian(line: str):
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "")
    if not vault_path:
        return

    trading_dir = os.path.join(vault_path, "Trading")
    os.makedirs(trading_dir, exist_ok=True)

    note_path = os.path.join(trading_dir, f"kraken-{_today()}.md")

    if not os.path.exists(note_path):
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(f"# Kraken Trade Log — {_today()}\n")

    with open(note_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _push_to_github():
    token = os.getenv("GITHUB_TOKEN", "")
    if not token or not _log_buffer:
        return

    repo    = "xx-r0ger-xx/kraken-swing-bot"
    path    = f"storage/logs/{_today()}.md"
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

    content = "\n".join(_log_buffer)
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/vnd.github+json",
    }

    sha = None
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            sha = json.loads(resp.read()).get("sha")
    except urllib.error.HTTPError:
        pass

    body = {"message": f"Trade log {_today()}", "content": encoded}
    if sha:
        body["sha"] = sha

    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(body).encode(),
            headers=headers,
            method="PUT",
        )
        with urllib.request.urlopen(req):
            log(f"Trade log pushed to GitHub: storage/logs/{_today()}.md")
    except urllib.error.HTTPError as e:
        log(f"GitHub push failed: {e.read().decode()}")


def _send_discord():
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
    if not webhook_url or not _discord_lines:
        return

    log_url = "https://github.com/xx-r0ger-xx/kraken-swing-bot/tree/main/storage/logs"

    body = {
        "embeds": [
            {
                "title": f"Kraken Swing Bot — {_today()}",
                "color": 5793266,  # purple
                "fields": [
                    {
                        "name": f"USD Balance: ${_current_balance:.2f}",
                        "value": "\n".join(_discord_lines) or "No activity.",
                    }
                ],
                "footer": {"text": f"Full log: {log_url}"},
            }
        ]
    }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req):
            log("Discord notification sent")
    except urllib.error.HTTPError as e:
        log(f"Discord notify failed: {e.read().decode()}")


# ── Public logging helpers ─────────────────────────────────────────────────────

def log_scan_start(balance: float, trade_size: float, holdings: int):
    global _current_balance
    _current_balance = balance

    msg = (
        f"Scan started | "
        f"USD Balance: ${balance:.2f} | "
        f"Trade size: ${trade_size:.2f} | "
        f"Active holdings: {holdings}/{os.getenv('MAX_POSITIONS', '3')}"
    )
    log(msg)
    _write_obsidian(f"\n## Scan — {_now()}\n**{msg}**\n")
    _buffer(f"# Kraken Trade Log — {_today()}\n")
    _buffer(f"## Scan — {_now()}\n**{msg}**\n")


def log_decision(symbol: str, signal, reason: str, price: float):
    icon = {"BUY": "[BUY]", "SELL": "[SELL]"}.get(signal, "[SKIP]")
    msg  = f"{icon} {symbol} @ ${price:.2f} — {reason}"
    log(msg)
    _write_obsidian(f"- {msg}")
    _buffer(f"- {msg}")
    _discord_lines.append(msg)


def log_order(symbol: str, action: str, price: float, volume: float, sl: float):
    msg = (
        f"ORDER {action} {volume:.6f} {symbol} @ ${price:.2f} | "
        f"SL: ${sl:.2f} (-{(1-(sl/price))*100:.1f}%)"
    )
    log(msg)
    _write_obsidian(f"  - **{msg}**")
    _buffer(f"  - **{msg}**")
    _discord_lines.append(f"  -> {msg}")


def log_skipped(symbol: str, reason: str):
    msg = f"SKIPPED {symbol} — {reason}"
    log(msg)
    _write_obsidian(f"- {msg}")
    _buffer(f"- {msg}")


def log_error(msg: str):
    log(f"ERROR: {msg}")
    _write_obsidian(f"- ERROR: {msg}")
    _buffer(f"- ERROR: {msg}")


def log_scan_end():
    log("=== Scan complete ===")
    _write_obsidian("\n---\n")
    _buffer("\n---\n")
    _push_to_github()
    _send_discord()
    _log_buffer.clear()
    _discord_lines.clear()
