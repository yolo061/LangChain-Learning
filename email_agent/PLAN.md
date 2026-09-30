# Email Agent · 开发清单

> 按依赖顺序排列，从上往下做。每项完成就把 `[ ]` 改成 `[x]`。
> 验证顺序 = 编号顺序，每项都有自己的自测方式，卡住先跑自测。
>
> 更新(2026-09-30)：主线全链已跑通——收件 → triage 分类 → 终端确认 → 真实回复。
> 目录从 `client/` 改名 `server/`,agent 层改为 LangGraph 图结构(triage_router + Command)。

## 1. `email_agent/config.py` — 环境配置 ✅

- [x] `Settings(BaseSettings)`：`deepseek_api_key`、`microsoft_id`（无默认值）、`model_name`、`base_url`、`temperature`（带默认值）
- [x] `model_config = SettingsConfigDict(env_file=".env", extra="ignore")` + 模块底部 `settings = Settings()` 单例
- [x] 文件在 `email_agent/` 包根，client 和 agent 平级引用；新增 `PKG_ROOT` 路径锚点供全项目使用
- 自测：`python -m email_agent.config` 打印 key 前 8 位

## 2. `server/auth.py` — 认证 ✅

- [x] `get_token()`：`_acquire_token()`（silent → 设备码兜底）+ 统一出口 `has_state_changed` 写盘
- [x] `CACHE_FILE` 改为 `PKG_ROOT` 锚定的绝对路径（根治换目录重复扫码）
- [x] Azure 侧：允许公共客户端流=是；删除 localhost:8400 重定向 URI（设备码流程不需要）
- 自测：连续跑两次，第二次不弹验证码 ✅

## 3. `server/connect.py` — Graph API 封装 ✅（原计划的 client/graph.py,并入 connect.py）

- [x] `BASE` 常量 + `graph_get(url, headers_extra)` / `graph_post` / `graph_patch`（统一 Bearer header、`raise_for_status()`）
- [x] `list_inbox(top)`（含 body + Prefer text 头）、`to_email_input(m)`（Graph JSON → State 四键 + id）
- [x] `create_reply_draft(message_id, body)` / `update_draft_body` / `send_draft(draft_id)`
- 自测：/me 200 → 列出邮件 → 真实回复已被 163 端收到 ✅

## 4. `server/connect.py` — 验收入口

- [x] `__main__` 可独立验收：打印账户、文件夹清单、邮件列表
- 遗留小项：`from .auth import` 相对导入已改但请坚持只用 `python -m` 运行

## 5. `agent/prompts_template.py` — 提示词常量 ✅

- [x] 全部为常量与模板 dict，不放任何函数和请求逻辑（课程 Lesson 2 官方 prompts 全集）

## 6. `agent/triage.py` — 分类层 ✅（升级为 LangGraph 图结构）

- [x] `Route(BaseModel)` + `llm_router = get_llm().with_structured_output(Route)`
- [x] `State(TypedDict)`：`email_input: dict` + `messages: Annotated[list, add_messages]`
- [x] `triage_router(state) -> Command`：respond → response_agent；ignore/notify → END
- 遗留小项：`State.email_input` 注解仍是 `str`，按 dict 用，改为 `dict`

## 7. `agent/tools.py` — 工具 ✅（write_email 已接真实发送）

- [x] 三个工具 + 注册器（`TOOL_REGISTRY` + `register` 在 `@tool` 上层 + `get_tools()`）
- [x] `write_email`：打印草稿 → 终端 y/n 确认 → `create_reply_draft` + `send_draft` 真实发送
- 遗留小项：确认逻辑目前是工具内 `input()`（过渡方案），下一步换 LangGraph interrupt 标准方案；
  依赖 `_current_email` 模块级注入，interrupt 改造时一并收掉

## 8. `agent/agent.py` — agent 组装 ✅

- [x] `get_prompt()`（`@dynamic_prompt`，profile 来自 `agent/profile.py`）+ `get_agent()`（`create_agent`）
- [x] `agent/graph.py`：`build_graph()` 组装大图（triage_router + response_agent）并返回 `compile()` 结果
- 自测：真实邮件跑通分类 + 工具调用 + 回信 ✅

## 9. `main.py` — 总入口 ✅（手动喂邮件版）

- [x] `list_inbox` → 手动选序号 → `to_email_input` → `build_graph().invoke` → 打印全程 messages
- [ ] （将来）外面包轮询循环：APScheduler 查未读 → 喂 agent
- 自测：`python -m email_agent.main` 完整跑通一次分类+工具调用 ✅

## 10. `test/agent.ipynb` — 实验场

- [ ] 定期清空：验证通过的代码沉淀到上面模块，不留正式逻辑

## 里程碑之外的待办（不影响主线）

- [x] 里程碑 2 验收（createReply 草稿 + 真实回复）✅
- [ ] 更新 README"当前进度"段
- [ ] 清理调试残留：auth.py 注释掉的旧代码、connect.py 文件夹清单调试块、临时 print
- [ ] 确认 `.env` / `token_cache.bin` 在 .gitignore
- [ ] 面试深挖项（按性价比做）：① LangGraph interrupt 人工确认（替代当前 input() 方案,优先）② store 按联系人记忆 ③ 邮件正文 prompt 注入防御 ④ LangSmith trace ⑤ webhook 服务器（搭配 FastAPI 确认页）
