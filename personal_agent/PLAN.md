# Personal Agent · 开发清单（第二个练习）

> 目标：做一个能从手机远程使用的个人 AI 助理（聊天 / 邮件 / 图片问答）。
> 核心架构一句话：**手机(PWA 前端) → 云服务器(中转 Broker) → 电脑(Agent Worker)**。
> 更新(2026-10-13)：设计定案。本文件由完整设计讨论沉淀而来，含架构决策 + 按依赖顺序的开发清单。
> 按依赖顺序从上往下做，每项完成把 `[ ]` 改成 `[x]`，卡住先跑自测。

## 0. 架构总览（定案）

```
手机(PWA网页) ──POST /tasks──> 云服务器(域名+nginx+FastAPI+SQLite) <──WS长连接── 电脑(Worker+Agent)
     ^                              │                                        │
     └────GET /tasks/{id} 取结果────┘ <────────────回写结果/状态──────────────┘
```

- 手机和电脑都只**主动连出**，谁都不需要被直连 → 同时解决外网访问、家庭 IP 变动、NAT 穿透三个问题。
- 消息不丢的保障在**数据库**（任务表持久化），不在内存：电脑断线期间任务保持 pending，重连后补发。
- 业界模式对照：这就是**消息队列/任务队列**（Gateway-Worker、生产者-消费者）——
  手机=Producer，服务器任务表=Broker，电脑=Consumer/Worker，task_id 查结果=Result Backend。
  同款现实案例：Telegram 机器人、Celery、GitHub Actions Runner、手机推送(APNs/FCM)。

### 选型记录（为什么不用别的）

| 方案 | 结论 |
|---|---|
| 局域网直连 | 被 DHCP 动态 IP 卡住；路由器绑定/mDNS(.local) 可解但出不了内网 |
| Tailscale | 自用组网法律风险极低，但国内协调服务器连通性不稳 → 放弃 |
| 云服务器中转 | **选定**。一台有公网 IP+域名的 VPS 全部搞定，服务器只做中转不跑模型，1核1G 够用 |

## 1. 通信协议（两端共同依赖，最先定死）

- [ ] 消息信封（JSON），WS 与 REST 共用字段语义：
  ```json
  {"type": "task", "task_id": "uuid", "session_id": "uuid",
   "action": "chat | image_qa | email", "payload": {"text": "...", "image_url": "..."}}
  ```
  `type`: `task / result / status / ping / pong`；`action` 决定 worker 路由到哪条 agent 流程
- [ ] 任务状态机：`pending → processing → done | failed`；processing 超 10 分钟无状态更新由服务器标回 pending（worker 崩溃兜底）
- [ ] REST 草案：`POST /tasks`（手机提交，返回 task_id）、`GET /tasks/{id}`（手机查结果）、`WS /ws`（电脑长连接，query 带 token）
- [ ] 认证：双 token（`worker` / `client` 两种角色）。WS **握手时**校验一次，连接即身份，之后消息不再验
- 自测：协议字段写进 `common/protocol.py` 常量，两端只 import 不重复定义

## 2. `agent_core/` — 电脑端 Agent 内核（先本地跑通，不碰网络）

- [ ] 移植 email_agent 的组织方式：`graph.py`（LangGraph 组装）、`tools/`、`prompts.py`（纯常量）
- [ ] 三条流程入口：`chat`（通用对话）、`image_qa`（图片下载→多模态模型问答）、`email`（二期接入，复用 email_agent 的图）
- [ ] 会话隔离：**一个编译好的 graph 全局共享，靠 `thread_id` 隔离**——
  `graph.ainvoke(inputs, config={"configurable": {"thread_id": session_id}})`，checkpointer 用 `SqliteSaver`
  （要点：状态绑 session 不绑连接；连接易逝、会话持久）
- [ ] 文件工具工作区约定（防沙箱脏乱）：`inbox/`(只读) `scratch/`(中间产物,可随时删) `output/`(仅 `finalize()` 可写)；
  清理由确定性代码执行（TTL/容量），模型只提议不执行删除
- 自测：终端里直接调 `graph.ainvoke`，同一 session_id 两轮对话有记忆，不同 session 互不串

## 3. `relay/` — 服务器端（FastAPI + SQLite，部署在 VPS）

- [ ] 任务表 `task(id, session_id, action, payload, status, result, created_at, updated_at)`
- [ ] REST：提交任务落库返回 task_id；按 id 查状态/结果
- [ ] `WS /ws`：验 token → 接收 worker 连接 → 推送 pending 任务 → 收 result/status 回写落库
- [ ] **掉线补发**：worker 重连成功后，把所有 pending 任务重新推一遍
- [ ] 应用层校验 Bearer token（挡扫描器）
- 自测：`curl -X POST /tasks` → sqlite 出现 pending → 模拟 worker 回写 → 查到 done

## 4. `agent_core/worker.py` — 电脑端常驻 Worker

- [ ] 单条 WebSocket 长连接（`wss://域名/ws?token=...`），断线指数退避重连
- [ ] **接收与处理解耦**（核心结构）：
  `receiver` 协程只管收消息入 `asyncio.Queue`；`worker` 协程从队列取任务、串行执行、回写结果
- [ ] 并发度 `asyncio.Semaphore(1)` 起步（单用户瓶颈在 LLM 调用），预留调到 2~5
- [ ] 心跳：30s ping/pong，双方及时发现对方挂了
- [ ] 收到 task 先回 `status: processing`，结束回 `result`（成功/失败都回）
- 自测：1 秒内连发 3 条任务 → 3 条都进队列 → 按序执行完，无丢失

## 5. `web/` — 手机端 PWA（先局域网验证，单文件 index.html）

- [ ] 提交任务（文字 + `<input type="file">` 选图）→ 存 task_id → 轮询 `GET /tasks/{id}` 渲染结果
- [ ] 图片上传到服务器存文件，任务消息只带 URL（不传 base64）
- [ ] MVP **不做流式**：处理中显示转圈，完成整段返回（流式留待进阶）
- 自测：手机浏览器访问 `http://VPS内网IP:端口` 全流程跑通一次

## 6. `deploy/` — 上线（nginx + HTTPS + 安全三件套）

- [ ] nginx 三个必踩坑一次配对：
  ① `/ws` 要透传 `Upgrade`/`Connection` 头 + `proxy_read_timeout 3600s`（否则 WS 连不上/每分钟断）
  ② `client_max_body_size 20m`（否则图片上传 413）
  ③ uvicorn 只绑 `127.0.0.1`，绝不 `0.0.0.0`
- [ ] HTTPS：`sudo certbot --nginx -d 域名`（自动改配置+续期）；80 强制跳 443
- [ ] 防火墙只开 80/443
- 前提检查：国内云 VPS 需域名已 ICP 备案，否则 80/443 被云厂商拦截
- 自测：手机切到流量（外网）访问 `https://域名` 全流程跑通 ✅ 这是项目的验收线

## 里程碑之外的进阶项（不影响主线，按性价比做）

- [ ] 流式输出：端到端 SSE/WebSocket 转发 token（链路每段都要改，MVP 后再说）
- [ ] LangGraph `interrupt()` 人工确认：邮件真实发送前在手机端确认（呼应 email_agent 待办的 input() 替换）
- [ ] 接入 email_agent：收件轮询(APScheduler) → 自动分拣 → 结果推手机
- [ ] 任务取消（cancel 消息类型）、失败重试策略
- [ ] 面试深挖项：① 为什么一条 WS 连接而非多条 ② 接收/处理为什么要解耦 ③ thread_id 会话隔离原理 ④ 这个架构与 Celery 的对应关系

## 目录结构

```
personal_agent/
├── PLAN.md            # 本文件
├── common/
│   └── protocol.py    # 消息信封、状态机常量（两端共享，只此一份）
├── agent_core/        # 电脑端
│   ├── graph.py       # LangGraph 组装（chat / image_qa / email 路由）
│   ├── tools/
│   ├── prompts.py
│   └── worker.py      # 常驻 WS 客户端（receiver + worker 双协程）
├── relay/             # 服务器端（部署到 VPS）
│   ├── main.py        # FastAPI：REST + WS
│   ├── db.py          # SQLite 任务表
│   └── auth.py        # token 校验
├── web/
│   └── index.html     # 手机端 PWA（单页）
└── deploy/
    └── nginx.conf
```
