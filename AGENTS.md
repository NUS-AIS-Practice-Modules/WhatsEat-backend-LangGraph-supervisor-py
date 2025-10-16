# AGENTS.md — WhatsEat Multi-Agent Repository Guide / WhatsEat 多智能体仓库指南

> This document aligns future contributors (human or AI) on architecture, workflows, and conventions for the WhatsEat backend and companion UI. / 本文档用于指导未来的人类或 AI 协作者，理解 WhatsEat 后端及配套前端的架构、流程与规范。

---

## 1. Project Overview / 项目概览

- **Purpose 目的**: Provide a LangGraph-powered supervisor that orchestrates restaurant discovery, recommendation, routing, and retrieval-augmented answers for the WhatsEat experience. / 通过 LangGraph 构建的 Supervisor 协同多个专长代理，完成餐厅搜索、推荐、路线规划与 RAG 问答。
- **Deliverables 交付物**:
  - Python package `whats_eat` exposing `create_supervisor` helpers and the compiled LangGraph app used by LangGraph Server. / Python 包 `whats_eat` 提供 `create_supervisor` 等封装以及 LangGraph Server 所需的编译图。
  - Frontend React demo (`frontend/`) consuming the supervisor API via LangGraph SDK. / React 前端示例（`frontend/`）通过 LangGraph SDK 调用 Supervisor。
- **Execution Context 执行场景**: Agents are invoked by the supervisor built in `whats_eat/app/supervisor_app.py`, then compiled in `whats_eat/app/run.py` for CLI/Server hosting. / 代理由 `whats_eat/app/supervisor_app.py` 的监督者调度，并在 `whats_eat/app/run.py` 中编译以供 CLI 或 Server 运行。

---

## 2. Architecture & Module Breakdown / 架构与模块划分

### 2.1 Backend package (`whats_eat/`) / 后端包
- `app/` — configuration, environment loading, supervisor assembly, and LangGraph export. / 提供配置、环境变量加载、Supervisor 装配与 LangGraph 导出。
  - `supervisor_app.py`: builds agents, creates forward tool, defines routing prompt, calls `create_supervisor`, and compiles to a runnable app. / 构建各代理、创建转发工具、定义路由提示词、调用 `create_supervisor` 并编译成可执行应用。
  - `run.py`: exposes `app = build_app()` for LangGraph CLI/Server discovery. / 暴露 `app = build_app()` 供 LangGraph CLI/Server 发现。
  - `env_loader.py`: loads `.env.json` > `.env` into process environment. / 优先读取 `.env.json`，再退回 `.env`，注入环境变量。
  - `config.py` / `schemas.py`: shared configuration and state contracts (extend as needed). / 公共配置与状态模型（按需扩展）。
- `langgraph_supervisor/` — reusable supervisor utilities. / 可复用的 Supervisor 工具集。
  - `supervisor.py`: wraps LangGraph’s `StateGraph`, ensures consistent tool binding, output mode trimming, and handoff validation. / 封装 LangGraph `StateGraph`，提供工具绑定、输出模式裁剪与转交校验。
  - `handoff.py`: default handoff and forward-message tools plus metadata helpers. / 定义默认转交工具、消息转发工具与元数据辅助。
  - `agent_name.py`, `utils.py`: agent naming exposure helpers. / Agent 名称处理与工具函数。
- `agents/` — REACT-style tool-using workers. / REACT 风格工具型执行代理。
  - `places_agent.py`: Google Places & Geocoding search (text, coordinates, photos). / 执行 Google Places / Geocoding 搜索与图片解析。
  - `user_profile_agent.py`: YouTube signals + OpenAI embedding profile. / 提取 YouTube 行为并生成 OpenAI 向量画像。
  - `recommender_agent.py`: ranks/filter candidates via custom tools. / 通过自研工具执行候选排序与筛选。
  - `summarizer_agent.py`: emits final JSON cards+rationale without tool calls. / 不调用工具，输出最终卡片与说明 JSON。
  - `route_agent.py`: builds HTML maps/routes once coordinates are known. / 在已有经纬度时生成路线 HTML。
  - `RAG_agent.py`: persists/query restaurants using Neo4j + Pinecone. / 使用 Neo4j + Pinecone 进行餐厅知识图谱写入与相似检索。
- `tools/` — stateless (idempotent) integrations. / 无状态（幂等）工具集。
  - `google_places.py`: HTTP client with retry/backoff, normalization, inline photo resolution. / 带回退重试、数据归一化、图片解析的 Google Places 客户端。
  - `user_profile.py`: YouTube Data API + embeddings orchestration. / 管理 YouTube 数据与嵌入。
  - `ranking.py`: ranking & filtering helpers for recommendations. / 推荐排序与过滤工具。
  - `route_map.py`: static map HTML generator. / 静态路线图 HTML 生成。
  - `RAG.py`: Neo4j, Pinecone, OpenAI utilities for ingestion/search. / 负责 Neo4j、Pinecone、OpenAI 的数据入库与检索。
- `CallAPIs/`: exploratory notebooks demonstrating API usage. / API 探索用 Notebook。

### 2.2 Tests (`tests/`) / 测试目录
- Pytest-based functional and integration tests for supervisor and agents (e.g., `test_supervisor.py`, `test_rag_agent.py`). / 基于 Pytest 的 Supervisor 与代理测试。
- Some tests require external services (Neo4j, Pinecone, OpenAI) and print diagnostic info; guard them with environment checks before running in CI. / 部分测试依赖外部服务并输出调试信息，CI 前需确认环境变量。

### 2.3 Frontend (`frontend/`) / 前端
- React + TypeScript app following LangGraph Generative UI tutorial, styled with Tailwind. / 基于 React + TypeScript，配合 Tailwind 的 LangGraph 教学式前端。
- `src/hooks/use_langgraph_chat.ts` encapsulates API calls to LangGraph Server. / `src/hooks/use_langgraph_chat.ts` 封装 LangGraph Server API 调用。
- Build scripts via `pnpm` (`start`, `build`). / 通过 `pnpm` 执行开发与构建。

### 2.4 Runtime integration / 运行集成
- `langgraph.json` declares the exported graph (`agent`) pointing to `whats_eat/app/run.py:app` and the `.env` file to load. / `langgraph.json` 声明导出的图 `agent`，指向 `whats_eat/app/run.py:app` 并指定 `.env`。
- LangGraph CLI (`uv run langgraph dev`) reads this manifest to serve the supervisor locally. / LangGraph CLI 依赖该清单在本地启动 Supervisor。

---

## 3. Technology Stack & Roadmap / 技术栈与路线

- **Python 3.11+**, LangGraph `0.6.x`, LangChain core/openai integrations. / Python 3.11+，LangGraph `0.6.x`，LangChain 生态。
- OpenAI chat + embedding models (default `openai:gpt-5-mini`, `text-embedding-3-*`). / OpenAI 对话与嵌入模型。
- Google Maps Places & Geocoding REST APIs (requires `GOOGLE_MAPS_API_KEY`). / Google 地点与地理编码接口。
- Neo4j Aura + Pinecone for RAG storage; optional if features unused. / RAG 功能使用 Neo4j Aura 与 Pinecone，可按需启用。
- React 18 + TypeScript + Tailwind for UI; bundler via CRA tooling. / React 18、TypeScript、Tailwind，基于 CRA 的构建流程。
- Packaging managed by `uv` + PDM backend; `requirements.txt` mirrors dependencies. / 依赖由 `uv` + PDM backend 管理，`requirements.txt` 为镜像列表。
- **Roadmap 提示**: notebooks and TODOs imply expanding KG/vector tooling (`RAG.py`) and optional agents (e.g., additional evidence retrieval). Plan experiments in notebooks before promoting to production code. / Notebook 与 TODO 暗示需强化知识图谱/向量功能，可先在 Notebook 中验证再迁移到正式模块。

---

## 4. Branching Strategy & Git Workflow / 分支策略与工作流

- Current checkout uses branch `work`; historical tooling (e.g., Makefile) compares diffs against `master`. Align with your remote default (`main` or `master`) before running `make lint_diff`. / 当前检出为 `work` 分支，Makefile 中的 `lint_diff` 会与 `master` 比较，请根据远程默认分支（`main` 或 `master`）调整。
- Suggested workflow / 推荐流程:
  1. Branch naming: `feature/<short-description>`, `bugfix/<issue-id>`, `docs/<topic>`; use lowercase kebab or snake for readability. / 新建分支命名建议 `feature/描述`、`bugfix/编号`、`docs/主题`。
  2. Rebase onto default branch regularly; resolve generated artifacts or notebooks outside commits when possible. / 定期与默认分支 rebase，避免提交生成产物或 Notebook 输出。
  3. Pull requests must include updated tests/docs and reference this `AGENTS.md`. / PR 需更新相应测试与文档，并引用本指南。
- Tag releases after passing integration tests; align backend and frontend tags when shipping coordinated features. / 集成测试通过后再打标签；前后端联动时同步版本号。

---

## 5. Build, Test, CI/CD, Deployment / 构建、测试、部署

### 5.1 Environment / 环境
- Copy `.env.example` → `.env` (frontend) and `.env.json` for backend secrets; `env_loader` prioritizes JSON. / 复制 `.env.example` 与 `.env.json`，`env_loader` 优先加载 JSON。
- Required keys: `OPENAI_API_KEY`, `GOOGLE_MAPS_API_KEY`, `NEO4J_*`, `PINECONE_*`, optional `YOUTUBE_API_KEY`. / 必需密钥：`OPENAI_API_KEY`、`GOOGLE_MAPS_API_KEY`、`NEO4J_*`、`PINECONE_*`；可选 `YOUTUBE_API_KEY`。

### 5.2 Backend build & serve / 后端
- Install dependencies with `uv sync` (or `pip install -r requirements.txt`). / 使用 `uv sync` 或 `pip install -r requirements.txt`。
- Local dev server: `uv run langgraph dev` (reads `langgraph.json`). / 本地开发服务器：`uv run langgraph dev`。
- Optional script `setup.ps1` automates Windows environment provisioning. / `setup.ps1` 可用于 Windows 自动化环境配置。

### 5.3 Frontend / 前端
- `pnpm install`, `pnpm start` for development; `pnpm build` for production bundle. / 通过 `pnpm install`、`pnpm start` 开发，`pnpm build` 生成生产包。

### 5.4 Testing / 测试
- Run `make test` or `uv run pytest -vv --disable-socket --allow-unix-socket`. / 使用 `make test` 或 `uv run pytest -vv --disable-socket --allow-unix-socket`。
- Linting: `make lint` (runs `ruff format`, `ruff check`, `uvx ty check`). / `make lint` 会执行 `ruff format`、`ruff check` 与 `uvx ty check`。
- Watch mode: `make test_watch` (pytest-watch). / `make test_watch` 启用实时测试。
- External service tests (Neo4j/Pinecone) skip automatically if keys missing; confirm before CI. / 依赖外部服务的测试若缺密钥会跳过，CI 前需确认。

### 5.5 Deployment / 部署
- Deploy backend via LangGraph Server or Cloud by publishing the compiled graph defined in `langgraph.json`; ensure environment variables accessible. / 通过 LangGraph Server 或 Cloud 发布 `langgraph.json` 所定义的图，确保环境变量可用。
- Serve frontend static bundle behind CDN or integrate into backend stack. / 前端生产包可通过静态托管或集成到后端。

---

## 6. Agent Usage Guide & Code of Conduct / Agent 使用指南与行为规范

1. **Preserve Supervisor Contracts** / **保持 Supervisor 合约**: Always create agents with `create_react_agent` and expose them via `build_<role>_agent()` functions. Avoid changing function signatures unless updating all call sites. / 代理需使用 `create_react_agent` 构建，并以 `build_<role>_agent()` 暴露，如需改动签名需同步所有调用方。
2. **State Discipline** / **状态管理约束**: Pass structured dictionaries only; avoid free-form text except final `summarizer_agent` payload. Use `messages` history sparingly to keep `output_mode="last_message"` lightweight. / 仅传递结构化字典，除最终输出外避免自由文本，控制 `messages` 数量以保持轻量。
3. **Tool Hygiene** / **工具使用规范**: Tools must validate inputs, handle retries (max 3 with exponential backoff), and cap payload sizes (e.g., ≤3 photos). / 工具需校验输入、支持最多 3 次指数退避重试，并限制返回规模（如照片 ≤3）。
4. **Error Surfacing** / **错误处理**: Bubble up external API failures via structured error fields rather than raising unhandled exceptions; supervisor should decide fallback. / 外部 API 失败通过结构化错误字段反馈，由监督者决定降级策略。
5. **Language Consistency** / **语言一致性**: Agents respond in user language when returning natural-language fields. / 返回自然语言内容时保持与用户语言一致。
6. **Documentation** / **文档义务**: Update this guide and relevant READMEs when adding modules or changing workflows. / 新增模块或调整流程需同步更新本指南及相关 README。
7. **AI Agent Contributions** / **AI 协作者注意**: Cite source files in summaries, avoid speculative claims, and do not alter credentials or large binaries. / 生成式 Agent 在总结时需引用来源，禁止臆测，不得修改凭据或大型二进制。

---

## 7. Coding Style & Quality Gates / 代码风格与质量要求

- **Formatting**: `ruff format` (line length 100, `E501` ignored). / 使用 `ruff format`，行长 100（忽略 `E501`）。
- **Linting**: `ruff check` with rules `E`, `W`, `F`, `I`, `B`. / `ruff check` 启用 `E/W/F/I/B` 规则。
- **Static typing**: `mypy` enforces typed defs (`disallow_untyped_defs = true`). / `mypy` 强制函数类型注解。
- **Type checker (`uvx ty check`)**: respects overrides in `tool.ty.rules`. / `uvx ty check` 依据 `tool.ty.rules` 的豁免。
- **Python conventions**: modules in `snake_case`, classes `PascalCase`, functions `snake_case` with imperative verbs; maintain docstrings for public APIs. / Python 命名：模块 `snake_case`，类 `PascalCase`，函数动词开头的 `snake_case`，公共 API 需 docstring。
- **Imports**: standard → third-party → local; no wildcard imports; avoid wrapping imports in try/except. / 导入顺序为标准库→第三方→本地，禁止通配符与 try/except 包裹导入。
- **Testing**: add pytest cases for new tools/agents; isolate network calls via fixtures or environment guards. / 新增工具/代理需补充 pytest，网络调用需通过 fixture 或环境开关隔离。

---

## 8. FAQs, Notes, Limitations / 常见问题与限制

- **Missing API keys?** Tools raise `RuntimeError` with clear messaging; tests may skip gracefully. / 缺少 API Key 时工具会抛出带提示的 `RuntimeError`，测试会优雅跳过。
- **Neo4j/Pinecone availability**: `RAG.py` will initialize indices; ensure service quotas before running integration tests. / `RAG.py` 会尝试初始化索引，运行集成测试前请确认服务配额。
- **Google Places quotas**: Photo fetches limited to 3 per place at 640×480; adjust constants responsibly. / Google Places 照片默认 3 张、640×480，修改需评估配额消耗。
- **Frontend/backed sync**: `summarizer_agent` JSON schema (`cards` array, `rationale` string) underpins UI; coordinate changes with frontend maintainers. / `summarizer_agent` 的 JSON 模式决定前端展示，变更需与前端同步。
- **Threading**: Supervisor compiles with `parallel_tool_calls=False`; enabling parallelization requires verifying agent/tool idempotency. / Supervisor 当前禁用并行工具调用，若需开启需确认代理与工具的幂等性。
- **Testing external notebooks**: `CallAPIs/` notebooks are exploratory and not part of automated tests; keep outputs cleared. / `CallAPIs/` Notebook 仅用于探索，不纳入自动化测试，提交前请清除输出。

---

## 9. Maintenance Notes / 维护记录

- **2025-10-14**: Repository-wide `AGENTS.md` rewritten to reflect current `whats_eat` layout, tooling, and quality bars; supersedes prior guidance referencing `users/whatseat`. / 2025-10-14：重写 `AGENTS.md`，更新为现有 `whats_eat` 结构与规范，取代旧版 `apps/whatseat` 相关指引。
- Keep this section chronological; include author, summary, and impacted areas for future edits. / 后续修改请按时间顺序记录，写明作者、摘要与影响范围。

---

> Stay aligned with this guide to ensure cohesive evolution of the WhatsEat supervisor ecosystem. / 请遵循本指南，确保 WhatsEat Supervisor 生态持续一致地演进。
