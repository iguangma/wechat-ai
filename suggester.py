#!/usr/bin/env python3
"""微信聊天 AI 回复建议 —— 阿里云百炼 (qwen)

只做「读懂消息 -> 生成回复建议」，不注入微信、不自动发送，零封号风险。
你仍然自己选一条、自己粘贴发送。

上下文策略:
  最近的 MAX_TURNS 轮原样带上；更早的部分自动压缩成「摘要」，避免长对话丢信息 / 爆 token。

用法:
  python3 suggester.py --text "在吗？周末有空吗？"
  python3 suggester.py --clip                       # 先在微信里 ⌘C 复制对方消息
  python3 suggester.py --clip --contact 张三 --persona "大学同学，很久没联系"
  python3 suggester.py --clip --copy 1              # 生成后把第 1 条复制到剪贴板，直接 ⌘V 发出去
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAT = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DEFAULT_MODEL = "qwen3.8-flash"
STYLES = ["简短直接", "温和得体", "幽默俏皮"]

# 原样保留的最近轮数；更早的会被压缩成摘要
MAX_TURNS = 12

# 摘要缓存（同一段老对话不重复调用模型）
_SUMMARY_CACHE = {}


def load_key():
    key = (os.environ.get("DASHSCOPE_API_KEY") or "").strip()
    if key:
        return key
    env_file = HERE / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DASHSCOPE_API_KEY"):
                return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit(f"未找到 DASHSCOPE_API_KEY（可写入 {HERE / '.env'}）")


def pbcopy(text):
    try:
        return subprocess.run(["pbcopy"], input=text.encode("utf-8")).returncode == 0
    except Exception:
        return False


def pbpaste():
    try:
        return subprocess.run(["pbpaste"], capture_output=True).stdout.decode("utf-8", "replace")
    except Exception:
        return ""


def _chat(messages, model=DEFAULT_MODEL, temperature=0.8, timeout=60):
    payload = {"model": model, "messages": messages, "temperature": temperature}
    req = urllib.request.Request(
        CHAT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {load_key()}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")
    return data["choices"][0]["message"]["content"]


def _who(entry):
    return entry.get("who") or entry.get("role") or "对方"


def summarize(entries, model=DEFAULT_MODEL):
    """把较早的对话压缩成简短要点（带进程内缓存）。"""
    cache_key = json.dumps(entries, ensure_ascii=False, sort_keys=True)
    if cache_key in _SUMMARY_CACHE:
        return _SUMMARY_CACHE[cache_key]

    convo = "\n".join(f"{_who(e)}: {e.get('text', '')}" for e in entries)
    messages = [
        {
            "role": "system",
            "content": (
                "你是对话摘要助手。把聊天记录压缩成简洁要点，保留：人物关系、约定/时间地点、"
                "未决事项、情绪与诉求、重要事实。不超过 5 行，不要编造，不要加小标题以外的解释。"
            ),
        },
        {"role": "user", "content": convo},
    ]
    text = _chat(messages, model, 0.3).strip()
    _SUMMARY_CACHE[cache_key] = text
    if len(_SUMMARY_CACHE) > 80:
        _SUMMARY_CACHE.clear()
    return text


def build_messages(text, persona, context, history, styles, contact="", summary=""):
    system = (
        "你是微信聊天助手，帮用户想「怎么回复对方」。"
        f"请给出 {len(styles)} 条可以直接发送的中文回复，风格依次是："
        + "、".join(styles)
        + "。要求：口语化、像真人聊天、不用书面语、不说教、不加解释、emoji 最多一个、每条不超过 40 字。"
        '只输出 JSON 数组，格式 [{"style":"风格","text":"回复内容"}]，不要任何多余文字。'
    )
    lines = []
    if contact:
        lines.append(f"【正在和谁聊】{contact}")
    if persona:
        lines.append(f"【我和对方的关系/人设】{persona}")
    if context:
        lines.append(f"【背景】{context}")
    if summary:
        lines.append("【更早的对话摘要】")
        lines.append(summary)
    if history:
        lines.append("【最近的对话】")
        for turn in history:
            lines.append(f"{_who(turn)}: {turn.get('text', '')}")
    lines.append("【对方刚发来的消息】")
    lines.append(text)
    lines.append("请给出回复建议。")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(lines)},
    ]


def _parse_items(content, styles):
    m = re.search(r"\[.*\]", content, re.S)
    if not m:
        return [{"style": "建议", "text": content.strip()}]
    try:
        arr = json.loads(m.group(0))
        return [{"style": str(x.get("style", "")), "text": str(x.get("text", "")).strip()} for x in arr]
    except Exception:
        return [{"style": "建议", "text": content.strip()}]


def suggest_ex(text, persona="", context="", history=None, styles=None, model=DEFAULT_MODEL, contact=""):
    """返回 {items, summary, total, recent}，方便前端显示「已压缩」提示。"""
    styles = styles or STYLES
    history = history or []

    summary = ""
    recent = history
    if len(history) > MAX_TURNS:
        old, recent = history[:-MAX_TURNS], history[-MAX_TURNS:]
        try:
            summary = summarize(old, model)
        except Exception:  # 摘要失败也要能出建议
            summary = ""

    messages = build_messages(text, persona, context, recent, styles, contact, summary)
    content = _chat(messages, model, 0.8)
    return {
        "items": _parse_items(content, styles),
        "summary": summary,
        "total": len(history),
        "recent": len(recent),
    }


def suggest(text, persona="", context="", history=None, styles=None, model=DEFAULT_MODEL, contact=""):
    return suggest_ex(text, persona, context, history, styles, model, contact)["items"]


def main():
    ap = argparse.ArgumentParser(description="微信聊天 AI 回复建议")
    ap.add_argument("--text", help="对方发来的消息")
    ap.add_argument("--clip", action="store_true", help="从剪贴板读取消息")
    ap.add_argument("--persona", default="", help="和对方的关系/人设")
    ap.add_argument("--contact", default="", help="正在和谁聊（如：张三）")
    ap.add_argument("--context", default="", help="背景信息")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--copy", type=int, default=0, help="生成后把第 N 条复制到剪贴板")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    text = args.text or (pbpaste() if args.clip else None)
    if not text or not text.strip():
        sys.exit('没有消息内容。用 --text "..." 或先在微信里复制对方消息再用 --clip')

    items = suggest(text.strip(), args.persona, args.context, None, None, args.model, args.contact)
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        for i, it in enumerate(items, 1):
            print(f"{i}. [{it['style']}] {it['text']}")
    if args.copy and 0 <= args.copy - 1 < len(items):
        if pbcopy(items[args.copy - 1]["text"]) and not args.json:
            print(f"\n已复制第 {args.copy} 条到剪贴板，直接 ⌘V 发送。")


if __name__ == "__main__":
    main()
