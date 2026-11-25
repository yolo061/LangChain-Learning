# Email Agent · 开发清单

> 按依赖顺序排列，从上往下做。每项完成就把 `[ ]` 改成 `[x]`。
> 验证顺序 = 编号顺序，每项都有自己的自测方式，卡住先跑自测。
>
> 更新(2026-09-30)：主线全链已跑通——收件 → triage 分类 → 终端确认 → 真实回复。
> 目录从 `client/` 改名 `server/`,agent 层改为 LangGraph 图结构(triage_router + Command)。
>
> 更新(2026-11-03)：人工确认升级为 LangGraph `interrupt` 标准方案（write_email 内
> `interrupt()` → 上层 `Command(resume=approve/reject)` 恢复），`_current_email` 全局
> 注入与 TOOL_REGISTRY 一并移除，改为闭包工厂 `get_tools(email_input)`；main.py 挂
> MemorySaver 驱动暂停/恢复循环。离线 mock 验证：暂停/拒绝/批准三路径全过。

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
- ~~遗留小项~~：`State.email_input` 注解已改 `dict`；`subject = state["email_input"]` 取值 bug 已修

## 7. `agent/tools.py` — 工具 ✅（write_email 已接 interrupt 人工确认 + 真实发送）

- [x] 三个工具，`get_tools(email_input)` 闭包工厂把当前邮件绑进 write_email（替代 TOOL_REGISTRY + `_current_email` 全局注入）
- [x] `write_email`：`interrupt()` 抛出草稿 → 上层 `Command(resume="approve"/"reject")` → `create_reply_draft` + `send_draft` 真实发送
- ~~遗留小项~~：input() 过渡方案已替换为 interrupt 标准方案；全局注入已随闭包工厂收掉

## 8. `agent/agent.py` — agent 组装 ✅

- [x] `get_prompt()`（`@dynamic_prompt`，profile 来自 `agent/profile.py`）+ `get_agent()`（`create_agent`）
- [x] `agent/graph.py`：`build_graph()` 组装大图（triage_router + response_agent）并返回 `compile()` 结果
- 自测：真实邮件跑通分类 + 工具调用 + 回信 ✅

## 9. `main.py` — 总入口 ✅（手动喂邮件版 + interrupt 审批循环）

- [x] `list_inbox` → 手动选序号 → `to_email_input` → `build_graph(checkpointer=MemorySaver())` → invoke → 处理 `__interrupt__` → `Command(resume=...)` 恢复
- [x] import 根统一为 `email_agent.*`（原先 `agent.*` / `email_agent.*` 混用，换目录运行必挂）
- [ ] （将来）外面包轮询循环：APScheduler 查未读 → 喂 agent
- 自测：`python -m email_agent.main` 完整跑通一次分类+工具调用 ✅

## 10. `test/agent.ipynb` — 实验场

- [ ] 定期清空：验证通过的代码沉淀到上面模块，不留正式逻辑

## 里程碑之外的待办（不影响主线）

- [x] 里程碑 2 验收（createReply 草稿 + 真实回复）✅
- [x] 更新 README"当前进度"段（2026-11-03）
- [x] 清理调试残留：auth.py 注释旧代码与 result 调试打印、connect.py 补 `graph_patch` + `raise_for_status`、triage 重复 import、graph.py IPython 改惰性导入
- [ ] 确认 `.env` / `token_cache.bin` 在 .gitignore
- 面试深挖项（按性价比做）：① ~~LangGraph interrupt 人工确认~~ ✅(2026-11-03,离线三路径验证通过) ② store 按联系人记忆 ③ 邮件正文 prompt 注入防御 ④ LangSmith trace ⑤ ~~webhook 服务器（搭配 FastAPI 确认页）~~ ✅(2026-11-03,升级为完整 Web 看板，落在 `F:\Email_Agent`，interrupt→HTTP 审批闭环真实跑通；本次配套给 State 加了 `triage` 字段)
