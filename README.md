# LangChain 框架学习笔记

基于 LangChain（1.x 新版包结构）的学习实践仓库，按 B 站课程合集（吴恩达 LangChain + LangGraph 四门课）分四个部分推进。第一部分的知识点整合在 `01_基于LangChain的大语言模型应用开发/00_LangChain_all_notes.md` 一个文件里，README 只做整体概览。

> 🔗 **GitHub 仓库**：https://github.com/lonely-square-three/LangChain-Learning （本仓库与 Gitee 双端同步更新）
>
> 🤖 **给 AI agent**：动工前先读 [PROJECT_PROFILE.md](PROJECT_PROFILE.md)（项目画像：现状、目录、架构、下一步、禁区）。

## 环境

- Python 3.12.x
- 依赖包：`langchain-openai`、`langchain-classic`、`langchain-core`、`openai`、`jupyter`
- 生成模型：DeepSeek（`deepseek-v4-flash`，API 兼容 OpenAI 协议，用 `ChatOpenAI` 指定 `base_url` 即可）；第 05 章起改用本地 Ollama（`qwen3.5:2b` 生成 + `qwen3-embedding:0.6b` 向量化），不依赖云端余额
- Embedding 模型：阿里云百炼（DashScope）Qwen 接口，仅第 04 章使用（DeepSeek 没有 embedding 接口）
- 密钥从环境变量读取（`DEEPSEEK_API_KEY` 等），不在代码中硬编码

## 目录结构与笔记导航

按课程合集分四个部分，每个部分一个文件夹：

- **`01_基于LangChain的大语言模型应用开发/`**（已学）：从"如何调用模型"到 RAG、评估、Agent。知识点整合在 [00_LangChain_all_notes.md](01_基于LangChain的大语言模型应用开发/00_LangChain_all_notes.md)，对应六个 notebook：
  - 01 提示词工程：原生 SDK 对比 LangChain（`01_LangChain_diff.ipynb`）
  - 02 会话记忆管理（`02_LangChain_Memory.ipynb`）
  - 03 链（Chains）（`03_LangChain_Chains.ipynb`）
  - 04 基于文档问答（RAG）（`04_LangChain_Response.ipynb`）
  - 05 LLM 应用评估（`05_LangChain_assess.ipynb`）
  - 06 Agent（`06_LangChain_Agents.ipynb`）
- **`02_LangChain的功能工具和代理/`**（进行中）：函数调用、LCEL、标记提取、工具路由（P9–P16）
- **`03_使用LangGraph进行长期代理记忆/`**：语义/情景/程序三层记忆（P17–P23）
- **`04_LangGraph中的AI代理/`**：LangGraph 生产级 agent、human-in-the-loop（P24–P32）

## 仓库其他目录

课程之外，仓库里还有三块内容：

- **`email_agent/`**：Outlook 邮件回复助手（LangGraph 实战项目）。计划与进度见 [email_agent/PLAN.md](email_agent/PLAN.md)，架构与面试讲解见 `面试准备/邮件助手_面试八股与项目详解.docx`。
- **`personal_agent/`**：第二个练习项目（手机 → 服务器中转 → 电脑 Worker），见 [personal_agent/PLAN.md](personal_agent/PLAN.md)。
- **`面试准备/`**：简历技能自测复盘、面试八股文档、LangChain/LangGraph 常见问题整理。
- **`归档/`**：与本仓库学习路线无关或已失效的历史文件，仅存档不再维护。
- **`codex对话记录/`**（本地，不提交）：从 Codex 导入的历史对话，索引见其中 `_索引.md`。

## 知识概览

这条学习路径的本质，是从"单次调用模型"逐步走向"围绕模型搭一套应用框架"。

**第 01 章解决"怎么调模型"**。先看原生 OpenAI SDK 的手动拼消息流程，再对比 LangChain 的封装：`ChatOpenAI` 创建模型、`ChatPromptTemplate` 管理提示词、`invoke()` 统一调用。这章还引入了结构化输出——模型返回的"JSON"其实是字符串，需要用 `StructuredOutputParser` 声明字段、注入格式说明书、再解析成字典，即"谁发说明书谁来阅卷"。

**第 02 章解决"模型记不住"**。大模型是无状态的，记忆组件把历史对话存起来、注入每次请求的提示词。四种记忆的取舍本质是同一个问题：记忆会无限增长，怎么控制？滑动窗口丢最早的、token 裁剪按量丢弃、摘要缓冲把旧对话压缩成摘要——分别对应"遗忘、限额、压缩"三种思路。

**第 03 章解决"多步骤任务"**。链把模型和提示词组合成可复用单元：`LLMChain` 是单步，`SimpleSequentialChain` 是单进单出的串联，`SequentialChain` 是多输入多输出且保留中间结果，`MultiPromptChain` 则让模型当调度员，把问题路由给最擅长它的子链。

**第 04 章解决"文档太大塞不进上下文"**。引入 RAG：文档切块 → embedding 向量化 → 存进向量库；查询时问题同样向量化，按相似度取最相关的几块，连同问题一起交给 LLM 生成答案。全链路既可一键（`VectorstoreIndexCreator`）也可拆开手动执行，`RetrievalQA` 链支持 stuff、map_reduce、refine、map_rerank 四种组合策略。

**第 05 章解决"效果好不好怎么知道"**。引入 LLM 应用评估：手工少量 + `QAGenerateChain` 自动批量生成测试问答对，跑出 predictions 后用 `QAEvalChain` 让另一个 LLM 当阅卷员——因为答案表述不唯一，字符串匹配会把正确答案判错，评估本身也要靠语言模型理解语义。`set_debug(True)` 可完整查看链每一步实际传给模型的 Prompt。全章已切换为本地 Ollama 模型运行。

贯穿五章的一条主线是**分工**：生成模型负责"写答案"，embedding 模型负责"理解与检索"，链负责"编排"，记忆负责"上下文"，评估链负责"阅卷"。学习时建议顺着 01 → 05 的顺序跑通代码，再回头看各章笔记复习原理。

## 学习进度

- [x] 原生 OpenAI SDK 调用与 LangChain 封装对比，`invoke()` 统一调用接口
- [x] 提示词模板 `ChatPromptTemplate`：占位符填充，本质是本地字符串替换
- [x] 结构化输出：`get_format_instructions()` 注入格式说明，`parse()` 解析成字典
- [x] 会话记忆：完整历史 / 滑动窗口 / token 裁剪 / 超限自动摘要
- [x] 链：LLMChain、SimpleSequentialChain、SequentialChain、MultiPromptChain 路由链
- [x] 文档问答（RAG）：embedding + 向量存储 + `RetrievalQA`，四种 chain_type 策略
- [x] LLM 应用评估：`QAGenerateChain` 自动生成测试用例、`QAEvalChain` LLM 评分、`set_debug` 调试、本地 Ollama 模型接入

> 注：`ConversationChain`、Memory 系列、`RetrievalQA` 等类来自 `langchain_classic`（旧版 API，官方已标记弃用，2.0 将移除），此处用于理解机制原理；新项目应使用 `create_agent` + checkpointer 等新式 API。
