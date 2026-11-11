#!/usr/bin/env python3
"""微信 AI 回复助手（本地网页版）

启动: python3 server.py  然后浏览器打开 http://127.0.0.1:8787
用法: 在微信里 ⌘C 复制对方消息 -> 页面自动出现 3 条回复建议 -> 点一下即复制 -> ⌘V 发送

零封号风险: 不注入微信、不自动发送，只在你手动复制时给建议。
上下文按「联系人」分开记录，可手动补记你自己发出去的话。
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import suggester

HOST, PORT = "127.0.0.1", 8787

PAGE = r"""<!doctype html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>微信 AI 回复助手</title>
<script>
try{
  var _t = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  document.documentElement.dataset.theme = _t;
}catch(e){}
</script>
<style>
*{box-sizing:border-box}
:root{
  --bg:#0c0e13; --card:#151922; --card2:#1b2030; --line:#242b39;
  --fg:#e9edf5; --muted:#8b93a7; --accent:#6b8cff; --accent2:#a78bfa;
  --ok:#34d399; --danger:#f87171;
  --shadow:0 1px 2px rgba(0,0,0,.5), 0 16px 40px rgba(0,0,0,.35);
  --glow:rgba(107,140,255,.18);
}
[data-theme="light"]{
  --bg:#f5f6fa; --card:#ffffff; --card2:#f2f4f9; --line:#e6e9f1;
  --fg:#1a1f2b; --muted:#6b7488; --accent:#4f74ff; --accent2:#8b5cf6;
  --ok:#059669; --danger:#dc2626;
  --shadow:0 1px 2px rgba(16,24,40,.05), 0 10px 30px rgba(16,24,40,.07);
  --glow:rgba(79,116,255,.14);
}
html,body{height:100%}
body{
  margin:0;
  font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
  color:var(--fg);
  background:
    radial-gradient(900px 500px at 15% -10%, var(--glow), transparent 60%),
    radial-gradient(700px 400px at 100% 0%, rgba(167,139,250,.10), transparent 55%),
    var(--bg);
  background-attachment:fixed;
  -webkit-font-smoothing:antialiased;
}
.top{
  position:sticky; top:0; z-index:20;
  backdrop-filter:saturate(1.4) blur(14px);
  -webkit-backdrop-filter:saturate(1.4) blur(14px);
  background:color-mix(in srgb, var(--bg) 78%, transparent);
  border-bottom:1px solid var(--line);
}
.top-in{max-width:900px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;gap:12px}
.brand{display:flex;align-items:center;gap:9px;font-weight:650;letter-spacing:.2px}
.dot{width:9px;height:9px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 0 0 4px var(--glow)}
.pill{font-size:11px;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:1px 8px}
.spacer{flex:1}
.contact{
  width:190px;background:var(--card);border:1px solid var(--line);color:var(--fg);
  border-radius:999px;padding:7px 14px;font:inherit;font-size:13px;outline:none;transition:.15s
}
.contact:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--glow)}
.icon-btn{
  width:36px;height:36px;border-radius:10px;border:1px solid var(--line);
  background:var(--card);color:var(--fg);cursor:pointer;font-size:15px;line-height:1;
  display:grid;place-items:center;transition:.15s
}
.icon-btn:hover{border-color:var(--accent)}
.wrap{max-width:900px;margin:0 auto;padding:20px 20px 70px}
.panel{
  background:var(--card);border:1px solid var(--line);border-radius:18px;
  padding:16px 18px;margin-bottom:14px;box-shadow:var(--shadow);
}
.panel-head{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.label{font-size:13px;font-weight:600;letter-spacing:.3px;color:var(--fg);opacity:.9}
.tools{display:flex;align-items:center;gap:8px;margin-left:auto;flex-wrap:wrap}
.btn{
  border:0;border-radius:10px;padding:8px 15px;font:inherit;font-size:13px;font-weight:600;
  cursor:pointer;color:#fff;background:linear-gradient(135deg,var(--accent),var(--accent2));
  transition:.15s;box-shadow:0 4px 14px var(--glow)
}
.btn:hover{transform:translateY(-1px);filter:brightness(1.05)}
.btn:active{transform:translateY(0)}
.btn:disabled{opacity:.5;cursor:default;transform:none;filter:none}
.btn.ghost{background:var(--card2);color:var(--fg);box-shadow:none;border:1px solid var(--line)}
.btn.ghost:hover{border-color:var(--accent)}
.switch{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);cursor:pointer;user-select:none}
input[type=checkbox]{accent-color:var(--accent);width:15px;height:15px;cursor:pointer}
.msg{
  white-space:pre-wrap;word-break:break-word;
  background:var(--card2);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:12px;padding:12px 14px;min-height:48px;font-size:15.5px
}
.msg.muted{color:var(--muted);font-size:14px;border-left-color:var(--line)}
.status{font-size:12.5px;color:var(--muted);margin-top:8px;min-height:16px}
.status.err{color:var(--danger)}
.sugs{display:flex;flex-direction:column;gap:10px}
.sug{
  display:flex;gap:12px;align-items:center;padding:13px 15px;
  background:var(--card2);border:1px solid var(--line);border-radius:14px;
  cursor:pointer;transition:.18s ease;position:relative
}
.sug:hover{border-color:var(--accent);box-shadow:0 8px 24px var(--glow);transform:translateY(-1px)}
.sug:active{transform:translateY(0)}
.sug .num{
  width:26px;height:26px;flex:0 0 auto;border-radius:9px;display:grid;place-items:center;
  font-size:12.5px;font-weight:700;color:#fff;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  box-shadow:0 3px 10px var(--glow)
}
.sug .body{flex:1;min-width:0}
.sug .txt{display:block;font-size:15.5px;line-height:1.5}
.sug .tag{display:block;font-size:11px;color:var(--muted);margin-top:3px;letter-spacing:.3px}
.sug .hint{font-size:11.5px;color:var(--muted);opacity:0;transition:.18s;white-space:nowrap}
.sug:hover .hint{opacity:1}
.sug.done{opacity:.55;border-color:var(--ok)}
.sug.done .num{background:linear-gradient(135deg,var(--ok),#22c55e)}
.sug.done .hint{opacity:1;color:var(--ok)}
.empty{color:var(--muted);font-size:13.5px;text-align:center;padding:16px 0}
details.panel>summary{
  cursor:pointer;list-style:none;font-size:13.5px;font-weight:600;
  display:flex;align-items:center;gap:8px;user-select:none
}
details.panel>summary::-webkit-details-marker{display:none}
details.panel>summary::before{
  content:"";width:6px;height:6px;border-right:1.6px solid var(--muted);border-bottom:1.6px solid var(--muted);
  transform:rotate(-45deg);transition:.2s;margin-right:2px
}
details.panel[open]>summary::before{transform:rotate(45deg)}
details.panel[open]>summary{margin-bottom:12px}
.chip{font-size:11px;color:var(--accent);background:var(--glow);border-radius:999px;padding:1px 9px;font-weight:600}
.field{margin-bottom:10px}
.field:last-child{margin-bottom:0}
.field>span{display:block;font-size:12px;color:var(--muted);margin-bottom:5px}
input[type=text],textarea{
  width:100%;background:var(--card2);border:1px solid var(--line);color:var(--fg);
  border-radius:10px;padding:9px 12px;font:inherit;font-size:14px;outline:none;transition:.15s
}
input[type=text]:focus,textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--glow)}
textarea{resize:vertical;line-height:1.55}
.hist{
  font-size:13px;max-height:200px;overflow:auto;border:1px solid var(--line);
  border-radius:12px;padding:10px 12px;background:var(--card2)
}
.hist .row2{display:flex;gap:8px;margin:2px 0}
.hist .who{flex:0 0 auto;font-size:11px;font-weight:700;color:var(--muted);width:30px;text-align:right;padding-top:2px}
.hist .who.me{color:var(--accent)}
.hist .said{flex:1;word-break:break-word}
.hist .empty-h{color:var(--muted);font-size:13px}
.rowline{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px}
.rowline input{flex:1;min-width:180px}
.toast{
  position:fixed;left:50%;bottom:30px;transform:translate(-50%,16px);
  background:var(--fg);color:var(--bg);padding:10px 20px;border-radius:999px;
  font-size:13px;font-weight:600;opacity:0;pointer-events:none;transition:.22s;z-index:50;
  box-shadow:0 10px 30px rgba(0,0,0,.35)
}
.toast.show{opacity:1;transform:translate(-50%,0)}
.foot{text-align:center;color:var(--muted);font-size:11.5px;margin-top:18px}
kbd{font:11px ui-monospace,Menlo,monospace;background:var(--card2);border:1px solid var(--line);border-bottom-width:2px;border-radius:5px;padding:0 5px}
@media (max-width:620px){
  .top-in{padding:10px 14px}
  .contact{width:130px}
  .wrap{padding:14px 14px 60px}
  .brand .pill{display:none}
}
</style>
</head>
<body>
<div class="top">
  <div class="top-in">
    <div class="brand"><span class="dot"></span>微信 AI 回复助手<span class="pill">本地 · 零封号风险</span></div>
    <div class="spacer"></div>
    <input id="contact" class="contact" list="contacts" placeholder="和谁聊？">
    <datalist id="contacts"></datalist>
    <button id="themeBtn" class="icon-btn" title="切换主题">☀️</button>
  </div>
</div>

<div class="wrap">
  <section class="panel">
    <div class="panel-head">
      <span class="label">对方发来的消息</span>
      <div class="tools">
        <label class="switch"><input type="checkbox" id="auto" checked> 自动监听</label>
        <button id="pasteBtn" class="btn ghost">读剪贴板</button>
        <button id="gen" class="btn">换一批</button>
      </div>
    </div>
    <div id="msgBox" class="msg muted">在微信里 ⌘C 复制对方的消息，这里会自动出现回复建议</div>
    <div id="status" class="status"></div>
  </section>

  <section class="panel">
    <div class="panel-head">
      <span class="label">回复建议</span>
      <div class="tools">
        <label class="switch"><input type="checkbox" id="addHist" checked> 记入上下文</label>
      </div>
    </div>
    <div id="sugs" class="sugs"><div class="empty">还没有建议</div></div>
    <div id="sumNote"></div>
  </section>

  <details class="panel">
    <summary>人设与背景</summary>
    <div class="field">
      <span>人设 / 和对方的关系</span>
      <input type="text" id="persona" placeholder="如：大学同学，很久没联系，关系一般">
    </div>
    <div class="field">
      <span>背景 / 语气要求</span>
      <textarea id="context" rows="2" placeholder="如：对方找我借钱，我想委婉拒绝"></textarea>
    </div>
  </details>

  <details class="panel" open>
    <summary>对话上下文 <span id="histWho" class="chip">默认</span> <span id="histCount" class="chip">0</span></summary>
    <div id="hist" class="hist"><div class="empty-h">（空）</div></div>
    <div class="field" style="margin-top:10px">
      <span>手动补一句（你刚自己回过去的话，不补就不会进上下文）</span>
      <div class="rowline">
        <input type="text" id="manual" placeholder="粘贴你刚发出去的话，回车记为我…">
        <button id="addMine" class="btn ghost">记为我</button>
        <button id="addTheirs" class="btn ghost">记为对方</button>
      </div>
    </div>
    <div class="rowline">
      <button id="undo" class="btn ghost">撤销上条</button>
      <button id="clear" class="btn ghost">清空此人</button>
    </div>
  </details>

  <div class="foot">数字键 <kbd>1</kbd><kbd>2</kbd><kbd>3</kbd> 复制对应建议 · <kbd>R</kbd> 换一批</div>
</div>

<div id="toast" class="toast"></div>

<script>
const $ = (s) => document.querySelector(s);
const DEFAULT_BUCKET = "（未命名）";
const state = { lastSeen: "", lastApplied: "", history: [], busy: false, current: "", contact: DEFAULT_BUCKET };

function escapeHtml(s){ return (s||"").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function setStatus(t, isErr){ const el = $("#status"); el.textContent = t || ""; el.classList.toggle("err", !!isErr); }

let toastTimer = null;
function toast(msg){
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 1900);
}

function applyTheme(t){
  document.documentElement.dataset.theme = t;
  localStorage.setItem("theme", t);
  $("#themeBtn").textContent = t === "dark" ? "☀️" : "🌙";
}

function buckets(){ try { return JSON.parse(localStorage.getItem("histories") || "{}"); } catch(e){ return {}; } }
function setBuckets(b){ localStorage.setItem("histories", JSON.stringify(b)); }

function refreshContacts(){
  const b = buckets();
  const names = Object.keys(b).filter(n => n !== DEFAULT_BUCKET && b[n] && b[n].length);
  $("#contacts").innerHTML = names.map(n => '<option value="' + escapeHtml(n) + '"></option>').join("");
}

function persist(){
  const b = buckets();
  const keep = state.history.slice(-50);
  if (keep.length) b[state.contact] = keep; else delete b[state.contact];
  setBuckets(b);
  refreshContacts();
}

function renderHist(){
  $("#histWho").textContent = state.contact === DEFAULT_BUCKET ? "默认" : state.contact;
  $("#histCount").textContent = state.history.length;
  const el = $("#hist");
  if (!state.history.length){ el.innerHTML = '<div class="empty-h">（空）</div>'; return; }
  el.innerHTML = state.history.map(t => {
    const me = t.who === "我";
    return '<div class="row2"><span class="who' + (me ? ' me' : '') + '">' + (me ? '我' : '对方') + '</span>' +
           '<span class="said">' + escapeHtml(t.text) + '</span></div>';
  }).join("");
  el.scrollTop = el.scrollHeight;
}

function resetView(){
  $("#sugs").innerHTML = '<div class="empty">还没有建议</div>';
  $("#sumNote").innerHTML = "";
  $("#msgBox").classList.add("muted");
  $("#msgBox").textContent = "在微信里 ⌘C 复制对方的消息，这里会自动出现回复建议";
  state.current = "";
  setStatus("");
}

function loadBucket(name){
  state.contact = name;
  state.history = (buckets()[name] || []).slice();
  renderHist();
  refreshContacts();
  resetView();
  const lastTheirs = state.history.filter(t => t.who !== "我").pop();
  if (lastTheirs){
    $("#msgBox").classList.remove("muted");
    $("#msgBox").textContent = lastTheirs.text;
    state.current = lastTheirs.text;
  }
}

function init(){
  applyTheme(document.documentElement.dataset.theme || "dark");
  const b = buckets();
  if (!Object.keys(b).length){
    try {
      const legacy = JSON.parse(localStorage.getItem("history") || "[]");
      if (Array.isArray(legacy) && legacy.length){ b[DEFAULT_BUCKET] = legacy; setBuckets(b); }
    } catch(e){}
  }
  $("#persona").value = localStorage.getItem("persona") || "";
  $("#context").value = localStorage.getItem("context") || "";
  const saved = (localStorage.getItem("contact") || "").trim();
  $("#contact").value = saved;
  state.contact = saved || DEFAULT_BUCKET;
  state.history = (buckets()[state.contact] || []).slice();
  renderHist();
  refreshContacts();
  loadBucket(state.contact);
}

function renderSugs(items){
  const el = $("#sugs");
  if (!items.length){ el.innerHTML = '<div class="empty">没有建议，点「换一批」重试</div>'; return; }
  el.innerHTML = items.map((it, i) =>
    '<div class="sug" data-i="' + i + '">' +
      '<span class="num">' + (i + 1) + '</span>' +
      '<span class="body">' +
        '<span class="txt">' + escapeHtml(it.text) + '</span>' +
        '<span class="tag">' + escapeHtml(it.style || ("建议" + (i + 1))) + '</span>' +
      '</span>' +
      '<span class="hint">点击复制</span>' +
    '</div>').join("");
  el.querySelectorAll(".sug").forEach(node => node.addEventListener("click", () => applySug(node, items[+node.dataset.i])));
}

function renderSummary(s){
  const el = $("#sumNote");
  if (!s){ el.innerHTML = ""; return; }
  el.innerHTML = '<details style="margin-top:10px"><summary style="cursor:pointer;font-size:12.5px;color:var(--muted)">🧠 更早的对话已压缩成摘要（点击展开）</summary>' +
    '<div style="margin-top:6px;white-space:pre-wrap;font-size:13px">' + escapeHtml(s) + '</div></details>';
}

async function applySug(node, it){
  state.lastApplied = it.text;
  await fetch("/api/copy", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({text: it.text})});
  node.classList.add("done");
  const h = node.querySelector(".hint"); if (h) h.textContent = "✓ 已复制";
  toast("已复制，回微信 ⌘V 发送");
  if ($("#addHist").checked){ state.history.push({who:"我", text: it.text}); persist(); renderHist(); }
}

async function generate(text){
  if (state.busy || !text) return;
  state.busy = true; $("#gen").disabled = true; setStatus("生成中…");
  try {
    const res = await fetch("/api/suggest", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({
        text: text,
        persona: $("#persona").value,
        context: $("#context").value,
        history: state.history.slice(-50),
        contact: state.contact === DEFAULT_BUCKET ? "" : state.contact
      })});
    const data = await res.json();
    if (data.error){ setStatus("出错: " + data.error, true); return; }
    renderSugs(data.items || []); renderSummary(data.summary); setStatus("");
  } catch(e){ setStatus("网络错误: " + e, true); }
  finally { state.busy = false; $("#gen").disabled = false; }
}

function captureMessage(text){
  state.current = text;
  $("#msgBox").classList.remove("muted");
  $("#msgBox").textContent = text;
  if ($("#addHist").checked){ state.history.push({who:"对方", text: text}); persist(); renderHist(); }
  generate(text);
}

function addManual(who){
  const t = ($("#manual").value || "").trim();
  if (!t) return;
  state.history.push({who: who, text: t});
  $("#manual").value = "";
  persist(); renderHist();
  toast("已记入「" + (state.contact === DEFAULT_BUCKET ? "默认" : state.contact) + "」");
}

async function poll(){
  if ($("#auto").checked && !state.busy){
    try {
      const r = await fetch("/api/clipboard");
      const d = await r.json();
      const t = (d.text || "").trim();
      if (t && t !== state.lastSeen){
        state.lastSeen = t;
        if (t !== state.lastApplied && t.length >= 2 && t.length <= 3000) captureMessage(t);
      }
    } catch(e){}
  }
  setTimeout(poll, 1500);
}

init();
$("#themeBtn").addEventListener("click", () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
$("#gen").addEventListener("click", () => generate(state.current));
$("#pasteBtn").addEventListener("click", async () => {
  const r = await fetch("/api/clipboard"); const d = await r.json();
  const t = (d.text || "").trim();
  if (t){ state.lastSeen = t; captureMessage(t); } else { toast("剪贴板是空的"); }
});
$("#addMine").addEventListener("click", () => addManual("我"));
$("#addTheirs").addEventListener("click", () => addManual("对方"));
$("#manual").addEventListener("keydown", e => { if (e.key === "Enter"){ e.preventDefault(); addManual("我"); } });
$("#undo").addEventListener("click", () => { if (state.history.length){ state.history.pop(); persist(); renderHist(); toast("已撤销上一条"); } });
$("#clear").addEventListener("click", () => { state.history = []; persist(); renderHist(); toast("已清空「" + (state.contact === DEFAULT_BUCKET ? "默认" : state.contact) + "」"); });
$("#contact").addEventListener("change", () => {
  persist();
  const name = ($("#contact").value || "").trim() || DEFAULT_BUCKET;
  localStorage.setItem("contact", name === DEFAULT_BUCKET ? "" : name);
  loadBucket(name);
});
$("#persona").addEventListener("change", () => localStorage.setItem("persona", $("#persona").value));
$("#context").addEventListener("change", () => localStorage.setItem("context", $("#context").value));

document.addEventListener("keydown", e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const tag = (e.target.tagName || "").toLowerCase();
  if (tag === "input" || tag === "textarea") return;
  if (e.key >= "1" && e.key <= "3"){
    const n = document.querySelectorAll(".sug")[+e.key - 1];
    if (n){ n.click(); }
  } else if (e.key.toLowerCase() === "r"){
    generate(state.current);
  }
});
poll();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif self.path.startswith("/api/clipboard"):
            self._send(200, json.dumps({"text": suggester.pbpaste()}, ensure_ascii=False))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            payload = {}

        if self.path.startswith("/api/suggest"):
            try:
                result = suggester.suggest_ex(
                    text=(payload.get("text") or "").strip(),
                    persona=payload.get("persona", ""),
                    context=payload.get("context", ""),
                    history=payload.get("history") or None,
                    styles=payload.get("styles") or None,
                    model=payload.get("model") or suggester.DEFAULT_MODEL,
                    contact=payload.get("contact", ""),
                )
                self._send(200, json.dumps({
                    "items": result["items"],
                    "summary": result["summary"],
                    "total": result["total"],
                    "recent": result["recent"],
                }, ensure_ascii=False))
            except Exception as e:  # noqa: BLE001
                self._send(200, json.dumps({"error": str(e)}, ensure_ascii=False))
        elif self.path.startswith("/api/copy"):
            ok = suggester.pbcopy(payload.get("text", ""))
            self._send(200, json.dumps({"ok": ok}))
        else:
            self._send(404, json.dumps({"error": "not found"}))


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"微信 AI 回复助手已启动 -> http://{HOST}:{PORT}  (Ctrl+C 退出)")
    server.serve_forever()


if __name__ == "__main__":
    main()
