# BatchLens — roadmap

更新：2026-09-21。ACTIVE 主项目；v0.1.0 已发行。按用户要求，v0.2.0 增加本地 Web UI 和 Mac/Windows 桌面安装包；科学模型范围不变。发布与平台验证状态以验证记录为准。

| 阶段 | 当前状态 | 剩余出口 |
|---|---|---|
| P0 研究与规格 | 六项目规划及 BatchLens 详细规格完成 | 随真实反馈修订 |
| P1 存在理由验证 | 竞品一手来源和用户亲历场景已记录；外部验证未完成 | 真实案例、对照任务、用户与专家评审；用户已授权受限探索性实现，见 docs/decisions.md |
| P2 最小纵向流程 | 已实现并测试 | 已有 sample/design → CLI → contrast → JSON |
| P3 MVP | 本地可用 | 七个 demo、报告、manifest、可选表、支持边界已核验 |
| P4 外部可用性验证 | 待做，不声称完成 | 真实 metadata、与最近替代品同任务比较、修正误解 |
| P5 发布工程 | Linux/macOS × Python 3.12/3.13 及独立 R 任务通过 | tag 发布流程和发布文件哈希已通过，见验证记录 |
| P6 v0.1.0 | GitHub + PyPI 发布、哈希和干净安装回验完成 | 继续外部用户/专家验证，不自动启动下一大型项目 |
| P7 v0.2.0 易用性 | Web UI、桌面窗口与三平台构建/安装验证流程已实现 | 完成发行验证；Developer ID/notarization、Windows 代码签名与真实用户试用仍需补充 |

证据见 [validation record](docs/validation-record.md)；逐项门见 [RELEASE_CHECKLIST](RELEASE_CHECKLIST.md)。本地构建与版本字符串都不算 release created。

## v0.3.0 统一产品

按用户确认，将 scDesign Audit 的快速导入、中英双语和细胞类型供体覆盖整合入 BatchLens；保留样本/YAML 高级入口，复用同一科学引擎。当前为候选版，本地和远程证据分别记录。后续只维护一个产品，不为原型另发同质化包。完成本轮后优先收集真实用户导入、配对声明和结论理解方面的反馈；不自动启动第二个 Top 5。

## 发布后

优先修复安装问题、科学错误与文档误解；再按真实用户需求决定是否扩展。h5ad metadata 导入、复杂重复测量、现有整合评估结果导入只在 backlog，不承诺下一版。没有批次校正、空间相关建模或通用平台计划。

外部试用若证明一个模板已足够，应收缩为 recipe 或上游扩展，不以已写代码作为继续扩张理由。未通过全部交付门前不启动 PathwayBridge。
