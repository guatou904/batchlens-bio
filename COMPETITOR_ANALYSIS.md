# BatchLens — competitor analysis

调研日期：2026-09-11。方法：GitHub README/官方文档、PyPI JSON 元数据、Bioconductor vignette 与原始论文。属于 desk research；没有安装跑分、系统功能穷举或用户访谈。未在文档看到某项功能 ≠ 对方没有该功能。活跃度、版本是时间快照，不拿 Stars 代替需求。

## 1. 结论先行

BatchLens 不应让研究者放弃 scIB/kBET/LISI。它应在整合和下游比较之前审计实验设计。真正需要比较的最近替代品是 **BatchQC + ExploreModelMatrix + 团队自己的 sample-sheet notebook**。如果相对这三者只有 Python CLI 和好看的 HTML，独立项目理由仍然偏弱。

可辩护的方向是领域专用产品交付：明确实验单位与技术观测的区别，把用户的具体比较、模型限制、层级冲突和机器可读 finding 连在一起。方法学来自已有统计学；价值需要真实任务验证，不能用“首个”宣传。

## 2. GitHub / ecosystem 比较

| 工具 / 一手来源 | 已确认能力 | 与 BatchLens 的关系 / 取舍 |
|---|---|---|
| [scIB](https://github.com/theislab/scib) / [指标 API](https://scib.readthedocs.io/en/latest/api/scib.metrics.metrics.html) | 整合 benchmark，包括 batch removal 和 bio-conservation；接收 batch/label 和整合前后数据 | 保留为整合评价方案；不重写其指标，不声称只看混合 |
| [scib-metrics](https://github.com/YosefLab/scib-metrics) / [Benchmarker](https://scib-metrics.readthedocs.io/en/latest/generated/scib_metrics.benchmark.Benchmarker.html) | Python-only 加速指标与多 embedding benchmark；官方提醒数值不能直接与原 scIB 混比 | “不用 R”“自动汇总指标”已不是差异点；未来如接入必须记录实现、版本和参数 |
| [kBET](https://github.com/theislab/kBET) | 邻域 batch 比例检验；官方也讨论分群计算、抽样、重复运行与输出统计 | 不能称其无局部检查或无不确定性；它不把独立实验单位和目标 contrast 作为核心产品输入 |
| [LISI](https://github.com/immunogenomics/LISI) | 局部标签多样性指标，可对 batch/生物标签计算 | 评价局部表示结构；不能从混合指标恢复完全混杂设计的缺失信息 |
| [CellMixS](https://github.com/almutlue/CellMixS) / [论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC7994321/) | 单细胞 batch bias 探索、细胞级 mixing 和整合前后结构比较、可视化 | “局部诊断”“细胞分层”已有先例；表达层诊断不应进入首版竞争 |
| [BatchQC](https://github.com/wejlab/BatchQC) / [vignette](https://bioconductor.org/packages/release/bioc/vignettes/BatchQC/inst/doc/BatchQC_Intro.html) | 实验设计展示、confounding statistics、表达诊断和校正 | 最直接竞争者之一；不能宣称现有工具不检查混杂。要实测专用层级/contrast 报告能否节省任务时间 |
| [ExploreModelMatrix](https://github.com/csoneson/ExploreModelMatrix) / [vignette](https://csoneson.github.io/ExploreModelMatrix/articles/ExploreModelMatrix.html) | sample table + formula，展示 rank、系数解释、协同出现和相关结构；支持静态图 | 最强设计解释替代品；BatchLens 的统计功能不能被称为创新，须证明领域输入契约与 headless findings 的价值 |
| [DESeq2](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html#model-matrix-not-full-rank) | 明确处理设计矩阵不满秩，解释完全混杂、嵌套与缺失水平 | 已有成熟错误检查与教育材料；BatchLens 争取更早、跨工具、无需 expression 的交付流程 |
| [MultiQC](https://github.com/MultiQC/MultiQC) | 聚合多样本生信输出为报告 | 可作为后续报告入口；不为“统一 HTML”另建大平台 |
| 普通 R/Python notebook | 交叉表、rank、人工解释可低成本实现 | 成本最低的替代品；必须和维护一个模板相比，而不只和手工 Excel 相比 |

上述“产品输入/流程差别”是文档范围内的观察，不是竞品不可实现的证明。决定前对前三个最近替代方案按相同案例实际试用。

## 3. 为什么还需要 BatchLens：具体对照

| 科研问题 | 适用现有工具 | BatchLens 候选增量 |
|---|---|---|
| Harmony/scVI 等表示的批次混合和生物保留怎样？ | scIB / scib-metrics | 首版不回答；指向现有工具 |
| time 与 processing run 完全重合，D7−D0 能在指定模型下估计吗？ | ExploreModelMatrix / DESeq2 设计检查 | 在读入 sample sheet 时返回 contrast 结论、依赖证据和稳定 finding ID |
| 3 donors、12 sections、5 万 spots，我有多少独立重复？ | 人工 metadata 检查 / 定制脚本 | 在声明的实验单位下显示层级计数，避免把技术重复当生物学 n |
| 一个无关协变量重复编码，是否所有比较都不可估计？ | 线性模型/contrast 专业工具 | 对每个 contrast 检查，不用 rank 单一红灯误导研究者 |
| 分析流水线需要可存档、可 diff 的设计限制记录 | 自写 notebook/report / BatchQC | JSON/TSV + rule version + input hash + exit policy；是否值得独立包待验证 |

不够强的卖点：Python 重写、自动出图、一键运行、LLM 解释、多指标总分。足够值得验证的组合：领域层级正确、指定比较正确、诊断证据可追溯、失败可机器识别。

## 4. PyPI 与安装生态快照

以下为当日直接请求 `https://pypi.org/pypi/<name>/json` 的返回值；只是声明兼容性，未经安装测试。

| 包 | 版本 | Requires-Python | 对规划的影响 |
|---|---|---|---|
| [scib](https://pypi.org/project/scib/) | 1.1.7 | >=3.9 | 不把整个 benchmark 栈拉入 metadata 工具 |
| [scib-metrics](https://pypi.org/project/scib-metrics/) | 0.6.1 | >=3.12 | 如果未来接入，需要单独验证版本/平台 |
| [anndata](https://pypi.org/project/anndata/) | 0.13.3.post0 | >=3.12 | h5ad 适配以后再加；首版可直接导出 obs metadata |
| [scanpy](https://pypi.org/project/scanpy/) | 1.12.4 | >=3.12 | 无需为样本表体检安装完整分析环境 |
| [multiqc](https://pypi.org/project/multiqc/) | 1.35 | !=3.14.1,>=3.9 | 可以文件集成，暂不做插件 |
| [pydeseq2](https://pypi.org/project/pydeseq2/) | 0.5.4 | >=3.11 | 下游 DE 仍交给专用工具 |

技术选择据此采用 Python 3.12–3.13 的小依赖核心（尚待 clean-install 验证）。没有 R/JAX/GPU 的首版来自任务收窄，不等于同功能比 scIB 更轻。

### GitHub 活跃度核验

当日直接查询公开 GitHub REST `repos/{owner}/{repo}`。`pushed_at` 可能包含任意分支活动，不等于正式 release 或维护质量；没有据此估计用户数。

| 仓库 | 默认分支 | archived | pushed_at（UTC） |
|---|---|---|---|
| theislab/scib | main | false | 2026-04-27 20:13:28 |
| YosefLab/scib-metrics | main | false | 2026-09-10 07:58:54 |
| wejlab/BatchQC | devel | false | 2026-08-28 19:16:48 |
| csoneson/ExploreModelMatrix | devel | false | 2026-04-28 17:58:45 |
| almutlue/CellMixS | devel | false | 2024-09-04 10:32:12 |

README、开发分支与 Bioconductor release 文档可能存在版本差异，实际对照要固定具体版本。GitHub license 字段的 `NOASSERTION`/null 不是无许可证结论，需查看发行版本 LICENSE/DESCRIPTION。

## 5. 名称与许可风险

PyPI `batchlens`、`batchlens-bio` 在本次 JSON 查询都返回 HTTP 404；不代表名字已保留、未来一定可注册，或没有其他品牌冲突。检索发现 [BatchLens 云系统批作业可视化论文（2021）](https://arxiv.org/abs/2112.15300)，因此建议对外使用 **BatchLens Bio** 作为候选消歧名称、发行名候选 `batchlens-bio`，产品规划名称仍保留用户指定的 BatchLens。发布前再核验，不在本阶段自行注册。

依赖优先使用公开 API，避免复制现有工具代码。scIB、scib-metrics、kBET、LISI 等许可证不同；选定实际依赖/引用代码后记录许可证和 attribution。当前只提出许可证评估任务，不作法律结论。

## 6. 证据缺口与决定

还缺：真实 sample/time/batch 案例的最小元数据；用户对独立 CLI 的偏好；现有工具同任务耗时；对诊断措辞的统计评审；多对多技术观测是否为首版必要输入。没有证明首创、市场规模或真实采用。

Decision：继续非代码验证；不启动产品实现。若差异主要可由一个通用模板覆盖，降为 biomed-agent-recipes 的设计体检 recipe；若层级验证与机器接口在多次真实任务中有明确增量，再独立实现。见 [VALIDATION_PLAN.md](VALIDATION_PLAN.md)。
