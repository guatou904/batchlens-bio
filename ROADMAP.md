# BatchLens — roadmap

更新：2026-09-12。ACTIVE 主项目；当前为本地和首轮远程 CI 验证通过的 v0.1.0 候选。仅按实际发布证据释放主项目席位。

| 阶段 | 当前状态 | 剩余出口 |
|---|---|---|
| P0 研究与规格 | 六项目规划及 BatchLens 详细规格完成 | 随真实反馈修订 |
| P1 存在理由验证 | 竞品一手来源和用户亲历场景已记录；外部验证未完成 | 真实案例、对照任务、用户与专家评审；用户已授权受限探索性实现，见 docs/decisions.md |
| P2 最小纵向流程 | 已实现并测试 | 已有 sample/design → CLI → contrast → JSON |
| P3 MVP | 本地可用 | 七个 demo、报告、manifest、可选表、支持边界已核验 |
| P4 外部可用性验证 | 待做，不声称完成 | 真实 metadata、与最近替代品同任务比较、修正误解 |
| P5 发布工程 | Linux/macOS × Python 3.12/3.13 及独立 R 任务通过 | tag 发布流程与下载回验 |
| P6 v0.1.0 | 公开仓库已上传；发布候选验证通过 | tag/Release、PyPI 配置与安装回验 |

证据见 [validation record](docs/validation-record.md)；逐项门见 [RELEASE_CHECKLIST](RELEASE_CHECKLIST.md)。本地构建与版本字符串都不算 release created。

## 发布后

优先修复安装问题、科学错误与文档误解；再按真实用户需求决定是否扩展。h5ad metadata 导入、复杂重复测量、现有整合评估结果导入只在 backlog，不承诺下一版。没有批次校正、空间相关建模或通用平台计划。

外部试用若证明一个模板已足够，应收缩为 recipe 或上游扩展，不以已写代码作为继续扩张理由。未通过全部交付门前不启动 PathwayBridge。
