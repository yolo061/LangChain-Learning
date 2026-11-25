# LangChain / LangGraph 实习面试常见问题整理

> 面向大模型应用开发方向实习/初级岗位，汇总自牛客、知乎、CSDN、小林 coding、Datawhale 及英文社区（Reddit / Medium / Interview Coder）的高频题，按 2025-2026 主流认知（LangChain 1.x + LangGraph）校准，旧写法均已标注。

## 面试考察意图总览

面试官问 LangChain/LangGraph 的问题，表面在考框架 API，实际在考四层能力：

1. **概念理解**：你是否明白每个组件"为什么存在"（比如为什么需要 LCEL、为什么 ReAct 会被函数调用取代），而不是背了一遍用法；
2. **系统设计**：给你一个场景（知识库问答、多轮助手），你能不能选对架构、说清权衡（固定链 vs Agent、RAG vs 微调）；
3. **评估意识**：这是 2025 年之后区分"调过 API"和"做过项目"的分水岭——你的 RAG/Agent 效果怎么量化？没有指标体系的迭代都是瞎调；
4. **踩坑经验**：检索质量差怎么排查、工具调用格式跑偏怎么兜底、多轮记忆爆上下文怎么办——答出具体排查路径比背概念更加分。

准备策略：每道题先能一句话答本质，再能展开 3 点细节，最后能落到"我在项目里是怎么做的"。

---

## 一、基础概念与框架认知

### 1. 什么是 LangChain？它解决了什么问题？

LangChain 是面向大模型应用开发的编排框架，核心不是替代模型，而是把模型调用、提示词管理、检索、工具调用、记忆、链式编排这些能力标准化地串起来。它解决的问题是：直接用原生 API 开发应用时，切换模型要改大量代码、提示词与业务代码耦合、RAG/Agent 这类模式都要自己从零造轮子。它提供了统一的 Runnable 接口，让组件可以自由组合、替换。回答时最好补一句认知：框架的价值在原型快速验证和生态集成，生产中很多团队会只用其中一部分（如 LCEL、集成层）而自己编排。

来源：[牛客 AI Agent 常考面试题 LangChain 篇](https://www.nowcoder.com/discuss/875876775417372672)

### 2. 谈谈你对「Chain」的理解，以及 LCEL 和旧式 LLMChain 的区别？

Chain 的本质是把"提示词模板 → 模型调用 → 输出解析"这类固定步骤组合成可复用的调用单元。旧式的 `LLMChain`、`SequentialChain`（现已移入 langchain-classic 标记弃用）是类式封装，组合能力和流式支持有限；新一代写法是 LCEL（LangChain Expression Language），用 `|` 管道把任意 Runnable 组件串起来，如 `prompt | model | parser`。LCEL 的优势：所有组件自动获得 invoke / batch / stream / astream 统一接口，原生支持流式输出、并行、重试与回退（`.with_fallback()`），且组合本身就是数据结构，便于序列化和追踪。面试加分点：能说出"Chain 的流程是开发者写死的，Agent 的流程是模型运行时决定的"这条边界。

来源：[小林 LangChain 面试题](https://xiaolinnote.com/ai/langchain/langchain_info.html)

### 3. LangChain 的核心组件有哪些？各自负责什么？

六大件：Model I/O（统一模型调用与提示词模板）、Retrieval（文档加载、切分、embedding、向量库、检索器）、Chains（步骤编排，LCEL 为现代写法）、Agents（让模型动态决定执行路径并调用工具）、Memory（会话状态与历史管理）、Callbacks（回调与可观测性）。回答时建议按"数据流向"串：提示词组织输入 → 模型产生输出 → 检索补充知识 → 编排决定流程 → 记忆维持状态 → 回调负责观测。能说出 1.x 版本包结构变化（核心能力拆到 langchain-core，旧类移入 langchain-classic，新项目推荐 LangGraph）是明显的加分项。

来源：[火山引擎 Agent 面试要点 LangChain 篇](https://developer.volcengine.com/articles/7582491181021659172)

### 4. LangChain 和 LlamaIndex 有什么区别？

定位不同：LlamaIndex 起家于数据索引和检索，围绕"把私有数据变成 LLM 可用的知识"设计，在文档解析、索引结构、检索策略上更精细，是 RAG 优先的框架；LangChain 起家于全流程编排，覆盖模型调用、Agent、工具、记忆等更宽的应用面，生态集成最多。选型上：纯文档问答/知识检索场景 LlamaIndex 上手更快；需要复杂编排、多工具 Agent、或想用 LangGraph 生态时 LangChain 更合适。两者也不互斥，常见做法是用 LlamaIndex 做检索层、LangChain/LangGraph 做编排层。

来源：[知乎大模型算法岗面试题](https://zhuanlan.zhihu.com/p/683078370)

### 5. LangChain 和 LangGraph 的核心区别是什么？

LangChain 的 Chain 表达的是**有向无环的固定流程**——步骤写死、依次执行；LangGraph 把编排升级为**图**：节点是步骤，边定义流转，支持循环、条件分支和状态回溯，状态（State）由开发者显式定义并由 reducer 合并更新。四个 Chain 做不了而 LangGraph 能做的事：循环迭代（agent 反复思考行动）、动态分支、持久化检查点（checkpointer）、人工介入（interrupt）。因此简单 RAG 用 Chain 就够，生产级 Agent 基本都迁移到 LangGraph——这也是官方把新能力都放在 LangGraph 的原因。

来源：[小林：LangChain 和 LangGraph 的核心区别](https://xiaolinnote.com/ai/langchain/langchain_vs_langgraph.html)、[LangChain 中文学习手册面试题](https://langchain.online/interview/langchain-langgraph-qa)

---

## 二、RAG 与向量检索

### 6. 为什么要用 RAG？它和微调怎么选？

RAG 解决三个问题：模型不知道私有/最新知识、上下文窗口装不下大文档、答案需要可溯源。和微调的分工：RAG 改变的是"模型能查到什么知识"，微调改变的是"模型的行为风格和领域能力"；知识高频更新、需要引用出处、预算有限时选 RAG，需要稳定输出特定格式/风格/领域话术时才考虑微调，两者也可组合。RAG 的标准流程：文档加载 → 切分（chunking）→ embedding 向量化 → 入向量库；查询时问题向量化 → 相似度检索 top-k → 拼进提示词 → 生成回答。答这道题最好主动补"RAG 的本质是信息检索问题，生成只是最后一公里"。

来源：[知乎大模型面试 118 题：RAG 核心原理](https://zhuanlan.zhihu.com/p/2057188629575886525)

### 7. 文档分块（Chunking）策略怎么选？块大小和重叠怎么定？

常——用做法是固定大小分块（512~1024 token，overlap 10%~20% 约 100~200）作为基线；更好的是按文档结构递归切分（按标题、段落、句子层级），保住语义边界；进阶有语义分块（按 embedding 相似度断句）和 Late Chunking。调参原则：技术文档/长上下文可以偏大，FAQ/问答对要小；块太小则上下文不完整，太大则检索精度稀释且浪费 token。关键展示点：说清"分块策略必须和评估绑定，换策略后用同一测试集对比命中率"，而不是背参数。

来源：[苏三说技术：RAG 夺命 10 连问](https://www.cnblogs.com/12lisu/p/19921242)、[Datawhale all-in-rag 文本分块](https://github.com/datawhalechina/all-in-rag/blob/main/docs/chapter2/05_text_chunking.md)

### 8. Embedding 模型怎么选型？

看四个维度：语言匹配（中文选中文优化的模型，如 Qwen/BGE 系列）、维度（影响存储和速度，不代表质量）、榜单成绩（MTEB/C-MTEB）、部署约束（本地跑选小模型，API 接受外部服务则选效果最好的）。工程上更重要的两点：**全库必须用同一个 embedding 模型**（问题和文档不同模型向量空间不通）、换 embedding 模型必须重建整个向量库。评估方式是拿真实查询集测检索命中率（recall@k / MRR），而不是只看榜单。

来源：[知乎 RAG 核心 118 题](https://zhuanlan.zhihu.com/p/2057188629575886525)

### 9. 检索策略有哪些？向量检索不准怎么办？

三个层次的策略：基础向量相似度检索（top-k）；MMR（最大边际相关）在相关性和多样性间平衡，避免检索出 10 个几乎一样的块；混合检索（向量 + BM25 关键词）互补语义理解与精确词匹配，再加 rerank 模型对候选重排序，是当前效果最稳的组合。排查检索不准的路径：先看原始查询是否含歧义/术语鸿沟（改写查询或 HyDE）、再查 chunk 是否切坏了语义、最后看 top-k 和阈值设置。能按这个顺序说出排查树，是区分做过项目的关键。

来源：[犬小哈：RAG 分块与检索排查](https://www.quanxiaoha.com/java-interview/rag-chunking-strategies)、[小林：RAG 最难的地方](https://xiaolinnote.com/ai/rag/20_hardest_parts.html)

### 10. RAG 系统怎么评估？（高频！）

分两层评估。**检索层**：用标注好的"问题 → 应命中的文档块"测试集，算 recall@k、MRR、命中率；**生成层**：忠实度（faithfulness，答案是否被检索内容支持，衡量幻觉）、答案相关性（answer relevancy）、上下文精确率/召回率（context precision/recall），常用框架是 RAGAS，或用 LLM 当裁判（LLM-as-judge）打分。重点：面试官问这题是想听"你有测试集、有指标、有前后对比"——例如"改写查询后命中率从 60% 提到 85%"。没有任何量化就宣称效果好，是这题最大的扣分项。

来源：[Reddit：LangGraph 项目被面试官追问](https://www.reddit.com/r/LangChain/comments/1k662xc/got_grilled_in_an_ml_interview_today_for_my/)、[Interview Coder LangGraph 35 题](https://www.interviewcoder.co/blog/langgraph-interview-questions)

### 11. RAG 落地中最难的地方是什么？

公认三大难点：**数据质量**（脏文档、表格、扫描件 PDF 的解析，往往占 80% 的工程量）；**检索质量调优**（分块、语义鸿沟、精确词召回三个问题交织，牵一发动全身）；**效果评估**（没有量化指标体系就不知道往哪优化）。回答时结合自己项目举例最有说服力，比如"我遇到细则文档里只有笼统类别没有具体证书名，通过查询改写把证书名映射到类别词解决"——把难点落到具体案例上。

来源：[小林：RAG 最难的地方](https://xiaolinnote.com/ai/rag/20_hardest_parts.html)

---

## 三、Memory 与状态管理

### 12. 大模型是无状态的，"记忆"是怎么实现的？

模型本身不记得任何历史，每次请求独立；"记忆"是把历史对话存下来、每次请求时注入提示词的工程手段。基础实现四种：完整历史（Buffer，简单但迟早爆上下文）、滑动窗口（只留最近 k 轮，会遗忘）、token 裁剪（按 token 上限从最早开始丢）、摘要压缩（旧对话用 LLM 压成摘要，兼顾"记得全"和"装得下"）。取舍的核心是同一个矛盾：记忆无限增长 vs 上下文有限。补充新认知：LangChain 1.x 里这些 Memory 类已标记弃用，短期记忆由 LangGraph 的 checkpointer 承担，长期记忆用 Store。

来源：[知乎：Agent 记忆管理高频面试题](https://zhuanlan.zhihu.com/p/2056052651524109554)

### 13. 短期记忆和长期记忆的区别？LangGraph 里分别怎么实现？

短期记忆是**单个会话内**的对话历史，LangGraph 通过 checkpointer 按 thread_id 自动保存图的状态，同一 thread 的多轮调用自动带上之前的状态；长期记忆是**跨会话**的用户信息与事实，用 LangGraph 的 Store（向量存储）保存，按 namespace 组织、任意 thread 可读写。一句话总结：checkpointer 管"这个对话进行到哪了"，Store 管"这个用户是谁、有什么偏好"。这也是 02 章 Memory 类被淘汰后的现代替代方案。

来源：[知乎：Agent 记忆管理高频面试题](https://zhuanlan.zhihu.com/p/2056052651524109554)、[CSDN：LangGraph 面试题](https://modelengine.csdn.net/690c4f505511483559e2a5c4.html)

### 14. 长期记忆有哪些类型？分别存什么？

认知科学启发的三层：**语义记忆**（用户相关的事实与偏好，"这个用户是学生、关注加分政策"，通常向量化存储供语义检索）；**情景记忆**（过去交互的具体经历，"上次他问过 X，当时的回答是 Y"，用于少样本示例或连续性）；**程序记忆**（系统自身的行为规则，从历史反馈中更新指令/提示词，即"学会怎么做"）。课程和论文里的经典递进是让邮件助手依次具备三层记忆。面试时能说清"分别用什么存储、何时写入、何时检索"比背定义重要。

来源：[知乎：Agent 记忆管理高频面试题](https://zhuanlan.zhihu.com/p/2056052651524109554)

### 15. 多轮对话记忆无限增长怎么处理？

四级手段按序使用：裁剪（保留最近 N 轮或 N token，丢弃最旧）；摘要压缩（旧对话由 LLM 压成摘要，保留近期原文）；结构化抽取（只把姓名、偏好等关键事实写进长期记忆 Store，对话历史本身可以丢）；重要度过滤（只对包含新信息的轮次写入）。生产系统通常"裁剪 + 摘要 + 结构化抽取"组合。加分点：提到 token 预算概念——给系统提示词、记忆、检索内容、用户输入分别设预算上限。

来源：[AtomGit：2026 大厂大模型/Agent 面试题](https://gitcode.csdn.net/6a236d7b662f9a54cb7a2bf1.html)

---

## 四、Agent

### 16. 你怎么理解 Agent？它和普通大模型问答最大的区别是什么？

普通问答是"一问一答"，流程在开发者手里；Agent 是让模型成为决策者——给定目标和工具，由模型自己规划步骤：思考 → 选择工具 → 观察结果 → 继续思考，循环直到给出最终答案（ReAct 循环）。三个关键区别：**流程控制权**从开发者转移到模型；**行动能力**（调工具、查库、执行代码）而不只是生成文本；**多步性**（复杂任务拆成多轮工具调用）。同时要会说边界：任务路径可预测时，固定工作流比 Agent 更可控、更便宜，"能用工作流就不用 Agent"是工程共识。

来源：[AtomGit：2026 大厂大模型/Agent 面试题](https://gitcode.csdn.net/6a236d7b662f9a54cb7a2bf1.html)

### 17. 讲讲 ReAct 的原理。

ReAct = Reasoning + Acting，通过提示词约定模型按固定格式输出：Thought（推理现在该干嘛）→ Action（选哪个工具）→ Action Input（工具参数）→ 等待 Observation（工具真实执行结果回填）→ 重复，直到输出 Final Answer。它的巧思在于把"推理痕迹"显式写出来，模型可以基于自己上一步的行动结果修正方向。局限：完全依赖提示词约定格式，小模型容易跑偏（格式错乱、忘了停）；每个循环都是一次完整 LLM 调用，慢且贵；需要 stop 词（如 `Observation:`）防止模型自己编造工具结果。这也是它逐渐被原生函数调用取代的原因。

来源：[Datawhale hello-agents 面试问题总结](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra01-%E9%9D%A2%E8%AF%95%E9%97%AE%E9%A2%98%E6%80%BB%E7%BB%93.md)

### 18. 函数调用（Function Calling）和 ReAct 提示词式工具调用有什么区别？

ReAct 靠提示词"教"模型输出约定文本，本质是提示工程，可靠性取决于模型指令遵循能力；Function Calling 是模型在训练阶段就学会了识别"该调工具"并输出**结构化的 JSON 调用请求**（函数名 + 参数），由框架解析后真实执行、把结果回传给模型继续生成。三个优势：结构化输出可程序化校验（参数类型错了能重试）；不再需要复杂的格式提示词和 stop 词；支持一次请求并行发起多个工具调用。现代实践（LangChain 1.x 的 `create_agent`、OpenAI/各家 API）都以函数调用为主，ReAct 更多作为理解 agent 循环的教学起点。

来源：[小林 LangChain 面试题](https://xiaolinnote.com/ai/langchain/langchain_info.html)

### 19. 怎么为 Agent 注册工具？工具的 description 为什么关键？

现代写法是把普通函数加 `@tool` 装饰器（或 `create_agent` 传 tools 列表），函数签名和 docstring 自动变成工具的名称、参数 schema 和说明书。description 是 agent 选工具的**唯一依据**——模型看不到工具内部实现，只看描述决定"这个问题该不该用它、参数怎么传"。写好 description 的要点：说清适用场景、输入格式、边界（例如"输入应为空字符串""日期计算请勿用本工具"）。工具选错的头号原因就是 description 含糊或多个工具描述重叠。

来源：[牛客 AI Agent 常考面试题](https://www.nowcoder.com/discuss/875876775417372672)

### 20. Agent 的工具调用怎么做得更稳？

多层防线：**模型层**——大脑用指令遵循强的模型，工具多、参数复杂时尤其明显；**协议层**——用原生函数调用替代提示词式 ReAct，结构化输出可校验；**框架层**——开启解析错误自动重试（如 handle_parsing_errors / LangGraph 的错误分支）、限制最大迭代次数防止死循环；**工具层**——工具内部做好参数校验和异常捕获，返回可读的错误信息让模型能自我修正（而不是抛异常炸掉整个 run）；**设计层**——减少工具数量、消除职责重叠、给容易误用的工具写清边界。能结合自己项目说"遇到过什么不稳、加了哪层防线"最好。

来源：[AtomGit：2026 大厂 Agent 面试题](https://gitcode.csdn.net/6a236d7b662f9a54cb7a2bf1.html)、[火山引擎 Agent 面试要点](https://developer.volcengine.com/articles/7582491181021659172)

### 21. 什么时候该用 Agent，什么时候用固定工作流？

判断依据是**任务路径的确定性**。固定工作流（prompt chain / 路由 / 并行）适合路径可枚举的任务：步骤固定、每次执行都一样，优点是可控、快、便宜、好调试。Agent 适合路径不可预判的任务：需要多步组合、工具选择动态、失败后需要换策略重试。工程原则是"能用工作流就不用 Agent"——每层 agent 决策都意味着更多 LLM 调用、更高延迟和成本、更难复现的错误。折中方案很常用：固定主干 + 局部 agentic（如只有检索失败才触发查询改写/联网兜底）。

来源：[Interview Coder LangGraph 35 题](https://www.interviewcoder.co/blog/langgraph-interview-questions)

---

## 五、LangGraph

### 22. LangGraph 的核心概念有哪些？

四个核心：**State**（开发者定义的共享状态 schema，用 Annotated + reducer 声明字段的合并逻辑，如消息列表用 add 追加而非覆盖）；**Node**（节点，接收状态、执行逻辑——调 LLM、跑工具、纯函数皆可——返回状态更新）；**Edge**（普通边固定流转，条件边按状态动态决定下一节点）；**图编译与执行**（`compile()` 检查拓扑后 `invoke/stream`，从 START 到 END）。所有节点读写同一个 State，这是它和 Chain"管道传递"的本质不同：State 是显式的、可持久化的。

来源：[腾讯云：LangGraph 入门 StateGraph](https://developer.cloud.tencent.com/article/2730810)、[知乎：Agent/LangGraph 八股 20 题](https://zhuanlan.zhihu.com/p/1914230995034564014)

### 23. checkpointer 是什么？解决什么问题？

checkpointer 是持久化机制：图每执行一步（super-step）自动把该 thread 的状态快照存下来。解决四类问题：**故障恢复**（服务重启后从断点继续）；**时间旅行**（回放任意历史状态，调试利器）；**多轮会话**（同一 thread_id 的下一轮调用自动恢复上下文，这就是短期记忆）；**人工介入**（图可以停在某个节点等人审批，再恢复执行）。常用实现是 MemorySaver（内存，开发用）和 SqliteSaver/PostgresSaver（生产）。能说出"checkpointer 管会话内、Store 管跨会话"的分工就是完整答案。

来源：[CSDN：langgraph 面试题](https://modelengine.csdn.net/690c4f505511483559e2a5c4.html)、[InfoQ：LangGraph 专题](https://xie.infoq.cn/article/64deee02f5cbf287704e71829)

### 24. thread_id 起什么作用？

thread_id 是会话的唯一标识，配合 checkpointer 实现**状态隔离**：不同 thread_id 各自维护独立的状态历史，互不干扰；相同 thread_id 的每次调用自动接续之前的状态。这是多用户系统的基本机制——每个用户会话一个 thread_id，服务端无需自己管理对话历史的存取。追问常考：换 thread_id 会怎样（开新会话，历史还在库里但不再注入）、怎么实现"用户手动开新对话"（换 thread_id 即可）。

来源：[luozhiyun：LangGraph 确定性输出](https://www.luozhiyun.com/archives/896)

### 25. Human-in-the-loop 怎么实现？

用 `interrupt()` 在关键节点前暂停图的执行，把待审批内容抛给外部；人工决策后通过 `Command(resume=...)` 恢复执行，图从断点继续。前提是图编译时接了 checkpointer（暂停状态要落盘，可能等几分钟甚至几天）。典型场景：敏感操作前审批（执行 SQL、发送邮件、给分认定）、工具调用结果存疑时人工确认。加分点：能说出这是 LangGraph 相对旧式 AgentExecutor 的核心优势之一——旧框架很难在循环中间优雅地暂停和恢复。

来源：[Interview Coder LangGraph 35 题](https://www.interviewcoder.co/blog/langgraph-interview-questions)、[知乎：Agent/LangGraph 八股 20 题](https://zhuanlan.zhihu.com/p/1914230995034564014)

### 26. 什么场景必须上 LangGraph 而不是 Chain？

四个信号：需要**循环**（agent 反复思考-行动-观察直到完成）；需要**动态路由**（根据中间结果走不同分支，且分支后还可能汇合、回跳）；需要**持久化**（长任务中断恢复、多轮会话记忆、审计回放）；需要**人工介入**。反例也要会说：纯 RAG 问答、固定预处理流水线，Chain/LCEL 更简洁高效——不要为了 LangGraph 而 LangGraph。

来源：[小林：LangChain vs LangGraph](https://xiaolinnote.com/ai/langchain/langchain_vs_langgraph.html)

---

## 六、工程实践

### 27. LLM 应用的成本和延迟怎么优化？

成本侧：模型分级（简单任务用小/便宜模型，复杂推理才用大模型；agent 里大脑用强模型、工具内部用小模型）、提示词瘦身、结果缓存（相同问题直接返回）、批处理。延迟侧：流式输出（首 token 时间决定体感）、并行工具调用、减少 agent 循环次数、检索层用缓存和量化索引。这套说辞的加分形态是给出量级感受：如"把 90% 的日常问答路由到小模型后，平均成本降到原来的 1/10"。

来源：[知乎大模型算法岗面试题](https://zhuanlan.zhihu.com/p/683078370)

### 28. 你怎么调试和观测一个 LLM 应用？

三层手段：**框架自带**——`set_debug(True)` 打印每步完整输入输出、verbose 看链的中间过程（适合开发期）；**追踪平台**——LangSmith 或自建 tracing，记录每次调用的完整 trace（提示词、检索内容、token 消耗、延迟），生产排查必备；**评估集回归**——每次改提示词/换模型都跑测试集对比，防止"改好一处坏一处"。面试官想听的词：trace、span、token 统计、回归测试。能说出"prompt 改动必须过评估集"就超过大部分候选人。

来源：[B站：2026 大模型求职指南](https://www.bilibili.com/video/BV1enbi6iEUM/)、[火山引擎 Agent 面试要点](https://developer.volcengine.com/articles/7582491181021659172)

### 29. 模型幻觉怎么缓解？

工程手段按性价比排序：RAG 提供事实依据并要求"只依据给定材料回答，材料中没有就说没有"（提示词约束 + 拒答机制）；答案附引用溯源（让模型标注依据来自哪个文档块，可人工核验）；temperature 调低；关键场景加校验层（LLM-as-judge 检查答案是否被检索内容支持，即忠实度校验）；结构化输出用函数调用而非自由文本。要说清：幻觉无法根除（模型机理决定），工程目标是"可检测、可溯源、可兜底"。

来源：[Datawhale hello-agents 面试问题总结](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra01-%E9%9D%A2%E8%AF%95%E9%97%AE%E9%A2%98%E6%80%BB%E7%BB%93.md)

### 30. 复杂文档（表格、扫描件 PDF）怎么做 RAG？

分文档类型处理：纯文本 PDF 常规切分即可；**扫描件**先 OCR；**表格**是难点——切分时不能把表切碎，常用做法是表格整块提取（或转 Markdown/HTML 保留结构）、按行转成"表头+键值对"文本再 embed，查询表格汇总数据时考虑走 SQL 而不是向量检索；**多模态内容**可用多模态模型给图表生成文字描述再入库。核心思想：解析层的产出质量决定 RAG 上限，这一层值得花 80% 的工程时间。

来源：[B站：企业级 Agent RAG 处理复杂 PDF](https://www.bilibili.com/video/BV1eRbr6mEJE/)、[知乎 RAG 118 题](https://zhuanlan.zhihu.com/p/2057188629575886525)

### 31. 介绍你的 RAG/Agent 项目：怎么衡量它变好了？

这是必考的项目叙述题，推荐 STAR 变体：**场景**（一句话：给谁解决什么问题）→ **架构与演进**（v1 固定 RAG → 发现什么问题 → v2 怎么改 → 数据变化）→ **评估方法**（测试集规模、指标：命中率/忠实度/人工抽检）→ **踩坑**（举一个具体排查案例）→ **边界**（知道什么场景不适用、错误答案怎么兜底）。三个禁忌：只报技术栈没有指标；说"效果很好"但说不出怎么量的；把课程 demo 原样当项目讲。面试官的潜台词是"你有没有真的跑过、量过、修过"。

来源：[Reddit：LangGraph 项目被追问](https://www.reddit.com/r/LangChain/comments/1k662xc/got_grilled_in_an_ml_interview_today_for_my/)、[牛客 AI Agent 常考面试题](https://www.nowcoder.com/discuss/875876775417372672)

---

## 参考来源汇总

- [牛客：AI Agent 常考面试题汇总 - LangChain 篇](https://www.nowcoder.com/discuss/875876775417372672)
- [小林面试笔记：LangChain 框架面试题](https://xiaolinnote.com/ai/langchain/langchain_info.html)
- [小林面试笔记：LangChain 和 LangGraph 的核心区别](https://xiaolinnote.com/ai/langchain/langchain_vs_langgraph.html)
- [小林面试笔记：RAG 落地最难的地方](https://xiaolinnote.com/ai/rag/20_hardest_parts.html)
- [Datawhale hello-agents：LLM & Agent 面试问题总结](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra01-%E9%9D%A2%E8%AF%95%E9%97%AE%E9%A2%98%E6%80%BB%E7%BB%93.md)
- [知乎：大模型面试 118 题 RAG 核心原理](https://zhuanlan.zhihu.com/p/2057188629575886525)
- [博客园（苏三说技术）：RAG 夺命 10 连问](https://www.cnblogs.com/12lisu/p/19921242)
- [犬小哈教程：RAG 分块策略](https://www.quanxiaoha.com/java-interview/rag-chunking-strategies)
- [GolangStar：知识库文本切块策略](https://golangstar.cn/backend_series/llm_interview/chunk.html)
- [Datawhale all-in-rag：文本分块](https://github.com/datawhalechina/all-in-rag/blob/main/docs/chapter2/05_text_chunking.md)
- [知乎：Agent/LangGraph 面试八股核心 20 题](https://zhuanlan.zhihu.com/p/1914230995034564014)
- [知乎：Agent 记忆管理高频面试题](https://zhuanlan.zhihu.com/p/2056052651524109554)
- [CSDN（ModelEngine）：langgraph 面试题](https://modelengine.csdn.net/690c4f505511483559e2a5c4.html)
- [InfoQ：LangGraph 专题八股](https://xie.infoq.cn/article/64deee02f5cbf287704e71829)
- [腾讯云开发者社区：LangGraph 入门](https://developer.cloud.tencent.com/article/2730810)
- [luozhiyun：LangGraph 是如何让 LLM 产生确定性输出的](https://www.luozhiyun.com/archives/896)
- [AtomGit：2026 大厂大模型/Agent 面试题](https://gitcode.csdn.net/6a236d7b662f9a54cb7a2bf1.html)
- [火山引擎：Agent 面试精选 LangChain 篇](https://developer.volcengine.com/articles/7582491181021659172)
- [LangChain 中文学习手册：常见面试题](https://langchain.online/interview/langchain-langgraph-qa)
- [Interview Coder：Top 35 LangGraph Interview Questions](https://www.interviewcoder.co/blog/langgraph-interview-questions)
- [Reddit：Got grilled in an ML interview for my LangGraph project](https://www.reddit.com/r/LangChain/comments/1k662xc/got_grilled_in_an_ml_interview_today_for_my/)
- [Medium：LangChain Interview Questions & Answers](https://souvikmajumder31.medium.com/langchain-interview-questions-answers-a72ea8aeddd9)
- [Hirist：Top 30 LangChain Interview Questions](https://www.hirist.tech/blog/top-30-langchain-interview-questions-and-answers/)
- [知乎：大模型算法岗面试题（含答案）](https://zhuanlan.zhihu.com/p/683078370)
- [B站：2026 大模型求职指南](https://www.bilibili.com/video/BV1enbi6iEUM/)
