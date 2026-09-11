# BatchLens — architecture draft

> 2026-09-12 状态更新：用户已授权完成首个项目并创建/上传仓库；受限 MVP 已实现，本地验证通过，远程发布待认证。以下保留规划背景；当前行为以 README、docs/input-schema.md、docs/methods.md 和 docs/decisions.md 为准。外部 G0/G1 验证并未完成。

2026-09-12；架构与实现对照。以 [PRODUCT_SPEC.md](PRODUCT_SPEC.md) 的 metadata-only v0.1.0 为边界。

## 1. 系统结构

```text
CSV/TSV samples + YAML design
       + optional observations / assay links
  → safe loaders → typed metadata validation
  → unit/relationship audit → descriptive coverage
  → supported-design gate → encoded X + explicit contrasts
  → linear algebra diagnostics → versioned findings
  → result.json / tables / offline report.html / manifest.json
```

没有网络服务、数据库、LLM、表达矩阵分析或 integration backend。加载、规则、计算、报告分层；HTML 只消费结构化结果，不能另做一遍科学计算。

## 2. 技术选择与取舍

| 部分 | 首版选择 | 理由 / 验证事项 |
|---|---|---|
| Runtime | Python 3.12–3.13 | 与当前 Python 组学生态衔接；只承诺测试过的平台 |
| CLI | 标准库 argparse | 命令少，无需额外 CLI framework |
| 表格 | pandas | 显式 dtype 读取、连接和覆盖表；不得把 ID 推断成数字 |
| 线性代数 | NumPy（SVD；无 SciPy 运行依赖） | SVD rank/null space；成熟实现，重点测诊断契约 |
| Schema/config | Pydantic v2 + PyYAML safe loader | 严格类型、未知字段拒绝、JSON schema；禁止执行 YAML 标签 |
| Formula | 声明式 additive terms 自行组装哑变量 | 不开放 Python/R 表达式求值；只做有限编码，不新造统计模型框架 |
| 报告 | Jinja2 + 少量内嵌 CSS/SVG | 离线单文件 HTML；无需 JS/CDN 或浏览器服务 |
| Build | pyproject.toml + Hatchling | wheel/sdist；CI 从制品安装，实际解析依赖后确定范围 |
| QA | pytest、Ruff、mypy、build、twine check | 科学反例优先；格式检查不替代数值与流程测试 |

依赖版本在实现门后做 resolver/安装验证再落定，不能把调研时 latest 全部直接锁死。开发环境保存精确锁文件；库依赖给经测试的兼容区间。首版不依赖 scIB/Scanpy/AnnData，所以也不承诺它们的计算能力。

## 3. 领域对象和粒度

`StudySpec`：schema_version、design_mode、sample_id/unit_id 列名、变量 role/type/reference、target、adjust_for、contrasts、可选表映射。

`SampleTable`：一行一个 sample。`UnitRegistry`：用户声明的实验单位及取样关系。`AssayLinks`：sample ↔ assay，可多对多；slide、section、run 是显式属性/实体，不强加普遍成立的 donor→sample→library→slide 单链。`ObservationTable`：cell/spot 标识及 sample 外键，仅覆盖检查。

需要区分三种数：表行数、distinct sample 数、distinct experimental unit 数。多个 technical replicates 不能增加最后一种。相同 unit 在配对的两个 target 水平出现是设计信息，不是错误；同一个 unit 重复切片也不是多个独立人。

v0.1.0 数值分析粒度：

- `independent`：所选样本中每个 unit 恰一行，target 为分类变量。
- `paired`：恰两个 target 水平，每个 unit 每水平恰一行，显式 unit fixed block；重复取样的协方差/检验不在本工具中拟合。
- 不满足上述结构仍生成层级和覆盖 findings，contrast 为 `NOT_ASSESSED`。不自动挑一张切片、不平均技术重复、不把 unit 自动插入 independent 模型。
- 样本跨多个 batch：链接表保留全部关系；若无法给所声明 sample-level 模型一个唯一 batch 值，数值阶段 `NOT_ASSESSED`。未来在真实需求证实后支持其他分析粒度；首版不可取多数 batch 伪造简单设计。

这样可以识别真实复杂性，同时避免首版变成任意重复测量模型引擎。

## 4. 设计矩阵与 contrast 的算法契约

固定截距；分类变量按显式 reference 作 treatment coding；数值协变量显式声明并记录中心/尺度处理。首版目标是一个分类变量的水平差，加性调整可含多个分类或数值协变量；不支持交互、随机效应、样条、任意公式函数。paired 模式加 unit block，但仍检测 batch 与 unit 等列依赖。

设 `X` 为 n×p 设计矩阵。SVD 给 rank r 和列依赖；默认绝对奇异值阈值 `eps * max(n,p) * s_max`，输出实际阈值、dtype 和 singular values。近奇异结果单独标 numerical sensitivity，不能伪装成完全混杂。连续变量尺度与条件数必须一同解释。

目标 `cᵀβ` 可估计当且仅当 c 在 X 的行空间内，即对 `Null(X)` 中所有 v 有 `cᵀv=0`。用 SVD row-space projector 的残差 `||c - P_row c||₂ / max(1,||c||₂)` 与记录的数值容差判断（首版拟定 1e-10，并以尺度/奇异边界反例验证）。不直接用某次广义逆输出的 β 值当“估计”。

普通 pairwise contrast：从同一 nuisance profile 的 target 两个水平编码行之差生成 c；加性模型保证 nuisance 抵消，仍记录比较方向与编码。若水平不存在、目标恒定或配置引用错误，输出输入错误。多 contrast 逐一判断。设计矩阵秩亏可能只影响 nuisance；**不能把所有比较一律判失败**。

秩亏时给具体列依赖、相关样本组合和受影响 contrast；可估计时也显示模型的加性假设。残差自由度 `n-r` 是设计行层面的诊断，不是 biological replication 或 power。

描述性覆盖：各 target×batch 的 sample 数和 distinct-unit 数、空组合、unit 与 batch/target 的关系。Cramér's V 可作为后续选项；首版不需要依赖一个“混杂分数”才能完成任务，也不套用通用 0.8 红线。

## 5. 规则契约

| Rule ID | 触发 / 证据 | 结论 |
|---|---|---|
| BL-META-001 | 必需字段缺失、主键重复冲突、外键悬空 | validation error；定位行/列 |
| BL-UNIT-001 | 同一 unit 多个 sample/技术观测 | 展示重复结构；是否不支持由 design_mode 决定，不自动认定违规 |
| BL-UNIT-002 | 某 target 水平 distinct unit <2 | 缺乏组内生物学重复 warning；不作功效推断 |
| BL-COVER-001 | 指定 target×batch 组合缺失 | coverage warning；单独不等于不可估计 |
| BL-DESIGN-001 | rank(X)<p | 展示依赖；严重性由受影响目标与数值证据决定 |
| BL-CONTRAST-001 | c 不属于 row(X) | critical / NON_ESTIMABLE，只针对声明比较 |
| BL-SUPPORT-001 | 输入设计超出支持粒度/语法 | warning / NOT_ASSESSED，返回已完成的描述结果 |
| BL-NUMERIC-001 | 数值边界或极端尺度 | warning，解释对容差的敏感性，保留诊断量 |

每项 finding 包含 `rule_id, rule_version, severity, scope, message, evidence_refs, limitations, suggested_next_step`。原始 ID 到共享别名的映射不随 report 默认导出。所有来自用户的字符串 HTML escape。

## 6. 输出契约与可复现性

`result.json` 含 schema/tool/ruleset versions、run_status、declared_design、counts、matrix_diagnostics、contrasts、findings、not_assessed。`tables/` 导出覆盖、编码、依赖证据；`manifest.json` 记录内容哈希、依赖版本、配置与运行时间。

核心 result 的排序固定，时间戳和绝对路径不进入确定性核心。输入哈希同时记录 raw bytes hash 与规范化 metadata hash，区分换行/排序变化和语义变化。对等数据行顺序不应改变科学结果。HTML 与 JSON 共用同一结果对象。

目标目录须不存在，父目录须存在；不提供递归清理/默认覆盖。用同文件系统临时输出目录，文件写完后排他创建目标目录并搬入文件，最后写 COMPLETE；这不是原子目录替换；失败保留可定位的临时产物并清楚说明，不能批量删除。所有删除严格遵守用户一次一个明确文件路径的规则。

## 7. 当前仓库结构

```text
batchlens-bio/
  PRODUCT_SPEC.md  COMPETITOR_ANALYSIS.md  ARCHITECTURE_DRAFT.md  ROADMAP.md
  README.md  LICENSE  CITATION.cff  CHANGELOG.md  CONTRIBUTING.md
  pyproject.toml  uv.lock
  src/batchlens/
    __init__.py  __main__.py  cli.py  config.py
    metadata.py  design.py  audit.py  reporting.py
    resources/report.html.j2  resources/demo/
  tests/test_science.py  tests/test_inputs.py  tests/test_cli.py
  docs/  examples/public_spatiallibd.py
  scripts/package_smoke.py  scripts/verify_r_oracle.R
  .github/workflows/ci.yml  release.yml  pypi.yml
```

Core 不依赖 portfolio 其他项目；dataset 与模板须纳入 wheel/sdist 的 package data。未来 adapter 只能经已稳定的 metadata/result 接口接入，不在首版设计抽象 plugin SDK。
