# Solution WIP — Novartis MDM Planning 2.0
Last updated: 2026-06-29 17:30
Current phase: 2

> **命名说明**：项目名"2.0"指第二轮招标（第一轮 Reltio 方案因成本过高被 Global 叫停，本次重新规划）。
> 本文 Phase 1 / Phase 2 指方案共创工作坊阶段，与项目实施阶段无关。

## Phase 1 — 需求对焦（已完成）

### 核心驱动力
EBX 许可证 ~2 年后到期，Global 无法负担资金，China 必须用有限预算完成迁移保业务可持续性。

### 需求修正
- REQ-005/006（复杂度证据化）→ 降权，客户已有自己的判断
- 客户核心判断：只替换 MDM 核心引擎（实体管理、Match & Merge、数据模型），外挂自开发逻辑尽量不动，只做新引擎集成。

### 确认的核心需求

**P0-A：AWS 自建 MDM 核心引擎可行性验证**
- 范围：核心引擎（实体管理、Match & Merge、数据模型），不含外挂逻辑
- 外挂逻辑（~100+ 子场景）仅做与新引擎的集成适配
- 验证方式：重新跑 PoC（基于 AWS 自建方案，非复用 Reltio PoC）

**P0-B：有限预算 + 长周期项目结构设计**
- 预算：~$1M USD 量级，需要 smart 方案控制成本
- 付款：客户财务要求，2026 H2 → 2028 年底分批付款
- 核心 balance：适当拉长项目周期（匹配付款节奏）vs 控制长周期带来的管理/沟通/变更成本

**P1：重用 2025 成果**（REQ-008）
**P1：EDM 治理对齐**（REQ-009）
**P1：方案对比报告**（REQ-010，AWS自建 vs 本地供应商）
**P2：ES 合规**（REQ-013）

### 选型评估框架（已确认权重）
功能契合30% / 灵活性20% / 安全合规20% / 可支持性15% / 成本周期15%

## Phase 2 — 方案草案

### 技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| 实体存储 | RDS PostgreSQL | HCP/HCO 实体 + 层级关系，配置驱动数据模型（参考 Pimcore 模式） |
| 批量 Match & Merge | OpenSearch（AWS China 托管）| 复用现有 SCDF 批量去重逻辑，对接新引擎 API |
| 非批量 Matching | 自建评分服务 | 替换 EBX Match Plugin；规则从 NVS MDM.excalidraw 复用 |
| 工作流 / DCR | Spring Boot 外挂（现有）| 尽量不动，仅替换 EBX API 调用为新引擎 REST API |
| 集成层 | MFT/MuleSoft/Solace → SCDF → 新引擎 | 保持现有 Source→SCDF pipeline，仅替换 SCDF 下游 |
| 运行环境 | AWS China（宁夏/北京 region）| 满足数据合规 + ES 合规要求 |

> 架构参考：Pimcore 的「配置驱动实体模型 + 关系型 DB + 独立 matching 引擎」模式已通过 Gartner MDM 2026 验证，我们用同等模式在 AWS China 自建。

---

### 竞争格局与差异化

**主要竞争对手：Cognizant**

**我们的核心差异化：Accenture 是 Novartis Global DCAM 服务供应商**
- 我们拥有与 Novartis Global EDM 团队的现有合作关系，Cognizant 没有
- WS-B（EDM/DCAM 治理对齐）不只是交付一份报告，而是**调动 Global EDM 团队主动参与评估、为方案背书**
- 策略：通过结构化的 DCAM 评审机制，让 Global Novartis 人员成为方案的"共同评估者"，而非事后审批者——这样 Go/No-go 时 Global 已经在局内，China 方案自然获得 Global 背书

**Global 现状**：Global EDM 团队已知晓项目，**不支持**（合规风险），但没有更好的替代方案（无法解决 MDM 产品成本问题）。我们的角色不是"拿到 Global 背书"，而是**帮助 Global 找到一条路：通过参与 DCAM 评估来提升项目合规性**，使其从反对方变为参与方。

**WS-B 执行方式（长周期连续会议）：**
1. 解读 DCAM 框架，逐条映射为 China MDM 方案的具体需求
2. 每轮 review 会议由 Global EDM 人员参与验证映射结果
3. 最终产出：**满足 DCAM 要求的 MDM 需求说明书**（不只是评估报告，而是经 Global review 的正式需求文档）
4. 这份需求说明书既是 WS-D/E 的输入，也是 Global 合规认可的证据

**为什么 Cognizant 无法复制**：没有 DCAM global 服务关系，无法以合法身份主持这一 review 流程，Global EDM 也不会愿意参与一个由陌生供应商主导的 DCAM 映射会议。

---

### RFP 范围澄清

**本次招标 = 规划阶段**，不含实施。交付物为：
- WS-A：存量成果复用评估报告
- WS-B：EDM/DCAM 治理影响评估报告
- WS-C：本地/混合 vs AWS 自建方案对比报告 ← 提案核心竞争力
- WS-D：AWS 自建目标架构蓝图（含集成 + 安全合规架构）
- WS-E：最小化 PoC 验证 + 功能设计规范 + Go/No-go 就绪报告

Go/No-go 决策目标：**2026年 Nov-Dec**。实施阶段（Stage B/C）为后续合同，本次不报价。

---

### 方案核心思路：最小替换，最大复用

```
现有架构：Source → MFT/MuleSoft/Solace → SCDF → [EBX Core + 外挂]
目标架构：Source → MFT/MuleSoft/Solace → SCDF → [新 MDM 核心] + [外挂（不动）]
                                                         ↑
                                              只替换这一块
```

**替换范围（实施边界）：**
- 实体管理引擎（HCP/HCO CRUD、数据模型、版本控制）
- Match & Merge 核心（评分规则配置 + 合并决策）
- EBX API 层 → 新 REST API（外挂从调用 EBX 改为调用新引擎）

**保持不动：**
- SCDF batch pipeline（批量去重逻辑 + Elasticsearch 索引）
- 所有 Spring Boot/Cloud 外挂业务逻辑
- MFT/MuleSoft/Solace 集成层
- 数据治理流程（DCAM 合规由 EDM 治理层承载，与引擎无关）

---

### 预算约束与人员规划

目标：~$1M USD（约720万RMB）

| 方案 | 团队 | 工期 | 月均 |
|------|------|------|------|
| 推荐 | 5人（1 PM/BA + 1 架构师 + 2 Dev + 1 QA/Ops） | 20个月 | ~$50K/月 |
| 备选 | 6人 | 18个月 | ~$55K/月 |

**成本控制策略（"Smart" 方案）：**
1. 复用 SCDF matching 逻辑 → 避免批量 matching 重写（节省约 3-4 人月）
2. 全开源技术栈（PostgreSQL + OpenSearch）→ 零许可证成本
3. 分阶段付款对齐客户财年 → 降低客户年度预算压力
4. PoC 阶段固定价格 → 双方低风险建立信任，再谈后续阶段
5. Strangler Fig 渐进替换 → EBX 并行期短，降低迁移风险 = 降低项目风险储备金

---

### 本次合同范围（规划阶段，~5个月，2026 H2）

| 月份 | 工作流 | 关键交付 |
|------|--------|----------|
| M1 | WS-A：存量成果盘点 + 复用评估 | 基线评估报告 |
| M1-M2 | WS-B：EDM/DCAM 治理对齐 | 治理影响评估报告 |
| M1-M3 | WS-C：方案对比（本地 vs AWS 自建）| 方案对比与推荐报告 |
| M2-M4 | WS-D：AWS 自建架构设计 | 目标架构蓝图 + 集成架构 + 安全合规架构 |
| M3-M5 | WS-E：最小化 PoC 验证 + 功能设计规范 | Go/No-go 就绪报告 |
| M5 | 综合：Go/No-go 决策会 | 决策材料包 |

> **WS-E 说明**：E1（PoC gap 评估）→ E2（针对性验证，非全量 PoC）→ E3（功能设计规范）→ E4（Go/No-go 就绪）

---

### 预算

**本次合同（规划阶段）：~100万RMB出头（约 $140K USD）**

5个月 × 约 3 人（顾问为主，PoC 阶段短期补充工程师）：

| 角色 | 人数 | 月份 | 说明 |
|------|------|------|------|
| Project Lead / BA | 1 | M1-M5 | 全程，WS-A/B/C 主责 |
| MDM 架构师 | 1 | M1-M5 | 全程，WS-C/D/E 主责 |
| PoC 工程师 | 1 | M3-M5 | WS-E 验证执行（3个月） |
| 数据治理顾问 | 兼职/复用 | M1-M2 | WS-B EDM 对齐，可由 Lead 兼 |

> blended rate ~7万RMB/月/人，3人×5月 + 1人×3月 ≈ 105万RMB ✓

**后续实施合同（Stage B+C，Go/No-go 通过后）：~$1M USD（约720万RMB）**
> 实施阶段独立合同，不在本次报价范围内。

---

### 后续实施阶段参考（Go/No-go 通过后）

> 仅作为规划参考，不在本次报价范围内。

**Stage B — 核心引擎 MVP（2027 H1，约6个月）**：上线新 MDM 核心，接入 1-2 个低风险外挂，EBX 并行

**Stage C — 全量迁移 + EBX 退场（2027 H2，约6-7个月）**：所有外挂切换，EBX 下线

EBX ~2028年中到期，Stage C 目标 2027年底完成，留约半年缓冲。

---

### Open Questions

**OQ-001 [已关闭]：Matching 逻辑归属**
决策：假设 EBX Matching 逻辑（SCDF + EBX Match Plugin 两层）保持不动，新引擎集成适配现有逻辑，不重写。PoC 验证集成接口，不验证 matching 规则本身。

**OQ-002 [中]：外挂逻辑清单**
当前约数十至百级别子场景（无正式盘点），哪些是 EBX API 调用，哪些是纯外挂自研逻辑？
- 本次规划阶段不需要完整清单（Stage B 才需要）
- **建议**：WS-E 期间作为 E1 交付物之一，完成外挂 high-level inventory（按模块分类，不需要逐条）

**OQ-003 [新]：PoC 成功标准（WS-E Go/No-go 对齐）**
需在 WS-E 启动前与客户对齐验证指标，避免 Go/No-go 会议上产生分歧：
- HCP 实体 CRUD 性能基线（TPS / latency 对比 EBX 现状）
- Matching 集成接口联调成功（SCDF → 新引擎 API）
- 功能覆盖度：FR-1~FR-7 中哪些可在 PoC 阶段验证，哪些留到实施
- **Child Data Space 去除验证**（见下方 WS-E 专项）

---

### WS-E 专项：Child Data Space 去除验证

**背景**：当前 EBX MDM 使用了 **Child Data Space**（子数据空间）概念——EBX 的原生特性，用于在 DCR 流程中创建主数据的"草稿版本"，审批通过后才合并回主空间。这一设计导致现有外挂方案中存在大量冗余逻辑（双版本管理、空间切换、合并冲突处理等）。

**新方案不引入 Child Data Space**，但这意味着：
1. 不能做简单的接口替换（EBX Child Data Space API → 新引擎等价 API），因为新引擎根本不存在这个概念
2. 依赖 Child Data Space 的外挂逻辑需要用**自开发方案**替代（例如：数据状态机 + 版本控制表）
3. 这是本次 PoC 最重要的验证点之一

**WS-E PoC 验证设计（Child Data Space 专项）：**
- 选取一个**现在依赖 Child Data Space、未来不使用**的典型场景（建议：HCP DCR 创建/审批流程）
- 验证目标 A：去掉 Child Data Space 是否能简化整体设计（预期：是，减少冗余状态管理）
- 验证目标 B：替代方案（自开发状态机）的开发成本是否可控（估算人月数，作为实施阶段报价依据）
- 输出：Child Data Space 替代方案设计 + 工作量估算，纳入 E3 功能设计规范和 E4 Go/No-go 就绪报告

**为什么这是 WS-E 差异化**：Cognizant 如果直接做接口替换的 PoC，会忽略 Child Data Space 这个关键依赖——最终发现无法简单替换，导致实施阶段工作量严重低估。我们提前在规划阶段验证并定量，是真正懂 EBX 架构的体现。

---

### WS-C 方案对比框架（REQ-010）

对比范围：**AWS 自建（从零构建核心引擎）vs Pimcore 开源方案（基于 Pimcore 二次开发）**
评估维度来自 REQ-015（权重已由客户确认）：

| 维度 | 权重 | Pimcore 开源方案 | AWS 自建方案（推荐）|
|------|------|-----------------|---------------------|
| **功能契合度** | 30% | ✅ 现成实体管理、matching、工作流；⚠️ China DCR 流程需深度定制，本地化成本高 | ✅ 按现有外挂逻辑量身构建，零适配摩擦 |
| **灵活性** | 20% | ⚠️ PHP/Symfony 技术栈，与现有 Java 外挂生态不一致；升级路径受开源社区节奏制约 | ✅ 技术栈自主可控，与 Spring Boot 外挂天然兼容 |
| **安全合规** | 20% | ⚠️ 可部署在 AWS China，但无中国本地社区和合规经验积累 | ✅ AWS China region 原生，ICP + 数据主权 + ES 合规路径清晰 |
| **可支持性** | 15% | ⚠️ 中国无 Pimcore 本地支持生态，问题排查依赖欧洲社区；长期维护风险高 | ✅ AWS managed services + Java 生态，国内人才池充足 |
| **成本与周期** | 15% | ⚠️ 开源免费但定制工作量大；China DCR 无现成模块，实际成本不低于自建 | ✅ 零许可证，复用现有 SCDF/外挂逻辑，总 TCO 更可预测 |

**推荐立场**：Pimcore 作为架构参考（配置驱动实体模型 + 独立 matching 引擎模式）有价值，但直接用于 Novartis China 的实施风险高于 AWS 自建——无本地支持生态、技术栈不一致、China DCR 需重建。AWS 自建方案复用现有投资，风险和成本更可控。
