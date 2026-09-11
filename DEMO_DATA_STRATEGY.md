# BatchLens — synthetic/public demo strategy

> 2026-09-12 状态更新：用户已授权完成首个项目并创建/上传仓库；受限 MVP 已实现，GitHub/PyPI v0.1.0 已发布，CI 与正式索引干净安装回验通过。以下保留规划背景；当前行为以 README、docs/input-schema.md、docs/methods.md 和 docs/decisions.md 为准。外部 G0/G1 验证并未完成。

2026-09-11；本文件定义数据计划，未生成或下载数据。首版体检不需要 expression 矩阵，demo 应围绕 metadata 的可辨识性和重复层级，而非漂亮 UMAP。

## 1. 默认 synthetic demo（随包、离线、可重复）

| case | 人为构造 | 期望结果 |
|---|---|---|
| balanced | target×run 交叉、有独立 units | ESTIMABLE；仍说明不保证 power/causality |
| confounded-time | D0 仅 A、D7 仅 B | NON_ESTIMABLE，有确切列依赖 |
| partial-overlap | 三个交叉组合，第四个空缺 | 加性模型 ESTIMABLE + coverage warning |
| redundant-nuisance | batch 与 machine 重复，target 完全交叉 | rank deficient，但 target ESTIMABLE |
| spatial-replicates | 3 units、12 sections、很多 spots | 正确计数；复杂 sample-level 推断 NOT_ASSESSED |
| paired | 每个 unit 在两水平各一行 | 正确 block/contrast；缺失配对变体 NOT_ASSESSED |
| metadata-errors | 冲突 sample、未知外键、缺失 unit | validate 失败，清楚定位错误 |
| mixed-assays | 一个 sample 跨 run / 一个 library 混多个 sample | 保留映射；不能自动把 batch 压成一个值 |

默认规模小于 100 sample，覆盖表可肉眼检查。随机数据如需生成采用固定 seed 并记录生成器版本；用于验收的设计表与期望标签固定，不靠随机碰巧制造混杂。测试和 demo 共用科学 fixtures，但用户 demo 必须走真实 CLI。发行包内置数据总量目标 <1 MB。

synthetic 标签必须出现在文件说明和报告页；不能把人为删组合后的数据叫真实发现。先发布最核心 balanced/confounded-time 两个可运行 demo，其余作为科学 fixtures；完整演示清单由 Release 检查覆盖。

## 2. 公开数据候选及状态

| 来源 | 可演示价值 | 已核实 / 尚待核实 |
|---|---|---|
| [spatialLIBD 官方仓库](https://github.com/LieberInstitute/spatialLIBD) | subject、section、spot 不同层级；官方 study design 描述 3 subjects 与相邻切片重复 | 已核实项目及设计说明；未提取 metadata，数据许可/再分发条件、精确字段和版本尚待核验 |
| [10x Human Breast Cancer Visium](https://www.10xgenomics.com/datasets/human-breast-cancer-visium-fresh-frozen-whole-transcriptome-1-standard) | 空间 assay 元数据格式和有限 biological replication 的教学 | 已核实官方数据页；不当作多 donor disease/control benchmark；字段与下载条款未审计 |
| [GSE96583 候选](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE96583) | 单细胞多样本设计候选，待重核后决定 | 本次 GEO 页面被浏览器验证拦截；不据此断言确切 donor/run/condition 映射或许可 |

首选推进 spatialLIBD 的 metadata 教学案例；若不足以演示 target 对比，明确展示层级检查，不编造 condition/batch。scRNA 公共案例保持候选，不为凑两个模态虚构批次标签。GEO 可公开访问不自动等于所有附件允许任意再分发。

## 3. 获取与出处契约

公开数据作为可选、显式下载路径，不在安装或离线 demo 中自动联网。每个正式案例记录：accession/DOI、原始 URL、提取日期、上游版本/文件名、SHA256、许可/使用条款、字段映射、过滤规则、哪些标签来自原文、哪些人为构造。缺失 run 用 unknown 表达，不能拿 donor ID 冒充 run。

能再分发且体积很小的 sample metadata 可以随案例发布；否则只提供用户自行获取和提取的步骤。表达矩阵、组织切片图和患者信息不随 package 分发。合成的对照删减必须单独标记 `derived-synthetic-scenario`，保持原始设计可查。

## 4. 公开数据不是统计 gold standard

真实数据没有通用“无 batch effect”标签；public demo 证明输入/输出与出处可复现，不证明诊断灵敏度。科学正确性的主证据来自人工可计算反例和独立 oracle。不能以一张 UMAP 作为结论真值。

## 5. v0.1.0 验收

- [ ] 离线 synthetic demo 从已安装发行包运行，输出完整报告。
- [ ] 至少一个来源/条款已核验的 public metadata 教学案例可按说明复现；如果不能再分发，提供独立获取说明与固定哈希。
- [ ] public 核心字段缺失明确说明，报告不捏造实验设计。
- [ ] synthetic 预期结论与实际输出逐项相符，HTML 可读。
- [ ] CI 默认不依赖外站；可选公开数据验收单独记录，外站失败不伪造成功。
