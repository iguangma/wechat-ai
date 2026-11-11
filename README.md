# 微信 AI 回复助手（本地版）

在微信里 ⌘C 复制对方的消息，浏览器里的小页面立刻给出 3 条可以直接发送的回复建议。
点一下复制，回微信 ⌘V 发出去。

**它不是自动回复机器人。** 不注入微信、不登录你的账号、不自动发送——只在你手动复制时给建议，零封号风险。

## 特点

- **副驾模式**：AI 只负责想，发不发、发哪句由你决定
- **三种语气**：简短直接 / 温和得体 / 幽默俏皮
- **按人记忆**：上下文按联系人分开存，和张三聊的不会串到李四那儿
- **长对话压缩**：超过 12 轮，早期内容自动压成摘要，预算、约定、忌讳都还记得
- **人设与背景**：关系、对方脾气、你想达到的目的，写一次一直生效
- **纯本地**：数据只存在你自己的电脑（浏览器 localStorage），不经过任何第三方服务器
- **零依赖**：Python 标准库即可，不用装包

## 截图

![界面截图](docs/screenshot.png)

## 运行

需要 Python 3.9+ 和 macOS（用到 `pbcopy`/`pbpaste` 读写剪贴板）。

```bash
git clone git@github.com:iguangma/wechat-ai.git
cd wechat-ai
cp .env.example .env      # 填入你的 DashScope Key
python3 server.py         # 或双击 start.command
```

然后打开 <http://127.0.0.1:8787>。

### 配置 API Key

去[阿里云百炼](https://bailian.console.aliyun.com/)控制台创建 API Key，写入 `.env`：

```
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

模型默认 `qwen3.8-flash`，走百炼的 OpenAI 兼容接口，国内直连。

## 用法

1. 在微信里选中对方的消息，⌘C
2. 网页会自动接住这条消息（也可以点「读剪贴板」），几秒后出现 3 条建议
3. 点一条 → 自动复制到剪贴板 → 回微信 ⌘V 发送

快捷键：`1` `2` `3` 复制对应建议，`R` 换一批。

自己回过去的话不会自动进上下文，需要手动「补一句」（记为我对 / 记为对方），否则 AI 只能看到对方说的话。

## 目录

```
server.py       本地 HTTP 服务 + 网页（HTML/CSS/JS 全在一个文件里）
suggester.py    拼提示词、调用通义千问、长对话摘要
start.command   macOS 双击启动脚本
.env.example    配置模板
```

## 说明

- 建议内容由大模型生成，不保证准确；涉及承诺、金额、时间的内容请自己核对后再发
- 聊天记录仅保存在浏览器本地，换浏览器或清理缓存会丢失

## 微信交流

![群](docs/we-discuss.png)


## License

MIT
