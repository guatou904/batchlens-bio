# BatchLens — PRODUCT_SPEC

> 2026-09-12 状态更新：用户已授权完成首个项目并创建/上传仓库；受限 MVP 已实现，本地验证通过，远程发布待认证。以下保留规划背景；当前行为以 README、docs/input-schema.md、docs/methods.md 和 docs/decisions.md 为准。外部 G0/G1 验证并未完成。

状态：ACTIVE（主项目）/ 本地发布候选；2026-09-12。用户确认定位：**单细胞/空间组学“实验设计与批次混杂体检工具”**。

## 1. 存在理由

科研人员仍应使用 scIB / kBET / LISI 评估整合结果。BatchLens 要回答它们之外的一个具体问题：**在声明的样本层级、设计模型和生物学比较下，现有实验设计是否能区分目标效应与批次；哪些重复和覆盖不足会限制解释？**

例：每个时间点有一万细胞，但 D0 全在 run A、D7 全在 run B。即使整合后的 batch mixing 很好，`~ time + run` 仍不能单独识别 time 的效应；新增细胞不提供缺失的交叉设计。BatchLens 应直接显示依赖关系、受影响的 contrast 和样本证据，而不是提供“校正成功”分数。这是实验设计结构检查，不是从 metadata 估计实际 batch effect 大小。[DESeq2 的完整混杂示例](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html#model-matrix-not-full-rank)

但此问题并非空白市场：BatchQC 有混杂诊断，ExploreModelMatrix 有设计矩阵分析。因此最大差异化是一个待验证的产品组合：**组学观测层级 → 重复单位检查 → 指定 contrast 的可估计性 → 证据化、可进入 CI 的本地报告**。不宣称新统计方法，不宣称竞品无法用脚本完成。完整比较见 [COMPETITOR_ANALYSIS.md](COMPETITOR_ANALYSIS.md)。

## 2. 用户与任务

| 用户 | 触发场景 | 需要的结果 |
|---|---|---|
| 单细胞分析者（主要） | 接到跨 donor、time、run 的样本表；准备整合或 pseudobulk DE | 知道指定比较能否在模型中区分 batch，缺少哪些样本信息 |
| 空间组学分析者（主要） | 多张 slide/section、很多 spots，准备比较疾病或时间点 | 区分 subject 与 section/spot 的重复关系；看清 condition 与 slide 覆盖 |
| Core facility / 计算合作者 | 接收项目或交付结果 | 可离线共享、带输入版本的体检附件；定位元数据冲突 |
| 实验设计者（次要） | 上机前审查样本分配表 | 提前看到完全混杂和空组合；补充跨批次对照的讨论依据 |

需求来源：用户亲历 sample/time/batch confounding；外部采用意愿、发生频率、愿意维护独立 CLI 的程度尚未访谈，不虚构 TAM 或用户数。

## 3. 唯一核心工作流

准备 sample metadata 和显式设计声明 → 校验层级/类型/缺失 → 汇总独立实验单位与技术观测 → 构建设计矩阵 → 检查指定 contrast → 阅读 HTML 并保留 JSON/TSV → 决定补 metadata、调整分析问题或寻求统计复核。

报告状态区分：

- `NON_ESTIMABLE`：指定线性 contrast 在声明模型下不可估计，有矩阵证据。
- `ESTIMABLE`：通过代数检查；不等于有足够功效、无未测混杂或有因果效应。
- `NOT_ASSESSED`：该模型/层级超出当前支持范围；未指定比较属于配置错误。
- Finding 严重度为 `info / warning / critical`；输入错误独立为运行错误，不能混为科学结论。

不输出“数据安全”“可以发表”“不存在 batch effect”的绿灯。不能以删除 batch、删除 donor 或整合为自动修复建议；改变模型就改变可解释的对象。

## 4. v0.1.0 MVP 边界

### Must-have

| 编号 | 功能 | 验收条件 |
|---|---|---|
| BL-01 | CSV/TSV 样本表 + YAML 设计声明 | 显式指定 ID、变量角色、类型、参考水平；未知字段/错误引用明确报错 |
| BL-02 | 实验单位与技术重复核对 | 单独统计 subject/experimental unit、sample、可选 library/section；重复行不增加生物学 n |
| BL-03 | 批次与目标变量覆盖 | 输出原始计数、distinct-unit 计数、空组合、嵌套关系；关联统计只作描述 |
| BL-04 | 受限加性固定效应设计矩阵 | SVD rank、列名/编码、依赖证据、数值容差；不拟合 expression 模型 |
| BL-05 | 一个分类 target 的 pairwise contrasts | 每个 contrast 独立判断可估计性；全矩阵秩亏不能直接宣布所有比较无效 |
| BL-06 | 简单配对设计检查 | 支持一个 unit block 的两水平配对比较；缺配对明确列出，重复测量不按独立样本处理 |
| BL-07 | 可选 observation metadata CSV/TSV | cell/spot → sample 的关联检查及 cell type/region 覆盖；不读取表达矩阵 |
| BL-08 | 可选技术观测关联表 | 支持 sample 与 library/slide 的非一一关系，审计 multiplexing/split sample；未支持的分析分辨率标 NOT_ASSESSED |
| BL-09 | 离线 HTML + JSON + TSV + manifest | Finding 有 ID、规则版本、证据引用、范围、局限和下一步建议；核心输出确定性 |
| BL-10 | CLI、测试、demo、文档、CI、包和 Release | [Release checklist](RELEASE_CHECKLIST.md) 全通过 |

### 明确不进入 v0.1.0

scIB/kBET/LISI 计算、UMAP/PCA、自动整合/批次校正、DE/DA、功效或样本量计算、因果效应估计、AI 解释、云服务、GUI、Scanpy/Seurat pipeline、原生 h5ad/SpatialData/图像读取、空间自相关检验、混合效应模型/随机效应、交互项/样条/任意 formula 执行、多物种、多组学自动分析。

空间组学的首版承诺仅为 metadata 的设计与重复层级审计。Cell type / region 覆盖是描述性检查，不自动在每个子群拟合模型或生成有效性评分。

## 5. 输入契约

主表一行一个实际 sample（取样单位/一次采样），`sample_id` 唯一；`unit_id` 表示用户声明的实验单位，可为 donor、animal、organoid 或受随机化的其他单位，不能硬编码 donor 永远是独立单位。重复取样允许同一 unit 多行。必须声明 `design_mode: independent | paired`；复杂层级可读入做覆盖检查，但代数推断限支持范围。

必需：sample ID、unit ID、目标变量、至少一个显式声明的 batch 因子、设计中的所有协变量。分类/数值类型必须声明；`time` 可是采样时间，`processing_date` 是技术日期，两者不自动互换。用户显式声明比较，不按列名猜测 condition 或 batch。

可选 observations 表：`observation_id`、`sample_id`、`cell_type` 或 `region`；所有引用须可连接，未知 sample 报错。observations 只影响覆盖表，不改变设计矩阵的行数或 rank。可选 assay links 表记录 `sample_id, assay_id, slide_id/section_id, batch`，多对多关系必须保留；不能随便取首个 batch 合并。

缺失 unit ID 无法保证重复单位，阻止完整 audit；`validate` 给缺失报告。其他必需字段缺失、sample 冲突、未知类别、未声明数据类型不静默填充。技术观测表与主表冲突也不能静默覆盖。

## 6. 输出与体验

首页先显示用户请求的比较、独立单位数、可估计性、最重要的设计限制；再显示样本/批次覆盖表、矩阵证据、未评估事项。避免把技术运行成功显示成科学检查通过。

所有结论都绑定输入 hash、design 配置、规则集版本和支持范围。共享默认使用别名化 ID，不写绝对输入路径，不嵌入 cell 级表；别名化不保证匿名，分类标签等仍需用户检查。运行全本地、无遥测。技术元数据仍可能敏感。

目标体验（待实测）：整理好 metadata 后，首次从安装到打开 demo ≤10 分钟；1000 sample / 50 设计列的核心 audit ≤10 秒、峰值内存 ≤512 MB（记录硬件）；不对百万 cells 的输入导入作无证据性能承诺。

## 7. 科学与产品风险

秩满仅说明指定模型中的参数结构；不验证随机化、测量正确性、协方差模型、统计功效或未测混杂。元数据关联强不证明存在表达批次效应，关联弱不排除批次效应。没有相关统计检验就不输出 p 值。加性假设不自动适用于交互、连续时间趋势或空间相关。

用户提供的重复单位和 formula 可能错误：报告始终复述其声明和条件性结论。首版宁可 `NOT_ASSESSED`，不能制造 certainty。少于 2 个独立单位的组标缺乏组内生物学重复；2 个并不表示充足，工具不发 power pass。

## 8. Go / no-go

初始规划结论（2026-09-11）：存在理由尚需验证。2026-09-12 按用户后续授权进入受限探索性实现；外部证据仍待完成，见 [VALIDATION_PLAN.md](VALIDATION_PLAN.md)。如果已有工具 + 简短模板能同样清晰地完成场景，应优先贡献上游或收入 recipes，而不是硬建独立包。v0.1.0 后也不因预留 roadmap 自动扩张。
