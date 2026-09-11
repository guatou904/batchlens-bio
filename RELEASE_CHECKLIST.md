# BatchLens v0.1.0 — definition of done

更新 2026-09-12。本地与首轮远程 CI 已通过；Release、PyPI 和外部评审仍待完成。证据见 [validation record](docs/validation-record.md)。用户后续授权受限探索性实现，见 [decisions](docs/decisions.md)；未把外部验证冒充完成。 每项必须记录 commit/tag、环境、日志/产物位置或 URL，不能只打勾。

## 产品与科学正确性

- [ ] G0/G1 价值验证记录齐全，主要使用场景有证据。
- [x] BL-01 至 BL-09 的受限 MVP 已实现；实际契约见 docs/input-schema.md 与 docs/methods.md。
- [ ] BL-10 完整交付（含实际远程 CI 和 Release）。
- [x] 完全混杂、部分覆盖、无关列冗余、配对与空间重复反例正确。
- [x] contrast 级结论通过独立 R model.matrix / QR 数值 oracle。
- [ ] 独立统计专家评审完成且无阻断问题。
- [x] ESTIMABLE 不被写成 power/causality pass；未知/不支持不假装通过。
- [ ] 无未解决的科学错误、数据丢失、安装阻断问题。

## 测试与 clean installation

- [x] pytest 科学/metadata/CLI/E2E 全通过；Ruff/mypy 通过。
- [x] Linux + macOS 的 Python 3.12/3.13 支持矩阵通过；支持范围以实测为准。
- [x] Windows 若未测试，在 README 写清未承诺；不能展示未经验证的支持徽章。
- [x] 从 wheel 在全新 venv 安装成功；从 sdist 独立构建并安装成功。
- [x] 在仓库外目录调用 entrypoint、--help、validate、audit、demo 成功。
- [x] package resources 完整；无依赖本地未提交文件/开发路径/网络 demo。
- [x] 非空输出拒绝覆盖；错误/critical/NOT_ASSESSED 对应退出码正确。
- [x] 核心 audit 性能/内存已记录平台、规模、版本和测量范围；不声称全链路性能。

## Demo 与文档

- [x] balanced/confounded synthetic demo 随包可重复，HTML 已人工检查。
- [x] public metadata 案例来源/条款/字段/哈希核验，可按步骤复现。
- [x] README：存在理由、与竞品边界、10 分钟 quickstart、截图、输入格式、输出、解释限制、支持环境、帮助入口。
- [x] methods：编码、rank/contrast 方法、容差、失败模式与版本。
- [x] CITATION.cff、CHANGELOG、CONTRIBUTING、LICENSE；准确署名，数据与代码授权区分。
- [ ] 所有命令在发行制品上实际执行；截图不得来自虚构输出。
- 暂不向 Recipes 新增内容；本次集中完成 BatchLens。

## GitHub Actions 与打包

- [x] 已创建并上传公开仓库 guatou904/batchlens-bio；包名 batchlens-bio，对外名称 BatchLens Bio。
- [ ] PR/push CI 执行 lint/types/tests、build、clean-install/demo；失败阻止合并。
- [ ] tag Release workflow 验证 package version/tag 一致，重复构建制品并核验内容。
- [ ] 在**实际远程 release commit** 上 Actions 成功；保存 run URL，不以本地成功代替。
- [x] wheel/sdist 通过 `twine check`，附 SHA256；发布权限最小化，发行凭据不进仓库。
- [ ] 发布身份配置可用；PyPI 分发采用正式支持的发行流程，具体平台配置在发布阶段查证。

## 真实发行与回验

- [ ] Git tag `v0.1.0` 对应经验证提交；不能只生成版本字符串。
- [ ] GitHub Release **实际创建**，有 release notes、wheel/sdist、hash、demo 链接和限制说明。
- [ ] 正式 PyPI 包 **实际发布**（发行名候选 batchlens-bio）；仅 TestPyPI 不算完成。
- [ ] 在新环境从正式索引安装指定版本，再跑 demo/audit，保存输出。
- [ ] 记录 tag、commit SHA、Release URL、PyPI URL、Actions URL、安装日志与 demo hash。
- [ ] 若发行出错，停止扩展并修复/按平台规则发行补丁；不覆盖已有版本或改写已发布 tag。
- [x] 维护者 guatou904；GitHub Issues 收集最小复现，优先安装/科学错误与文档修复；根 portfolio 据真实证据更新。

外部验证尚未完成的探索性候选不视为全部验收；只有上述全部完成，BatchLens 才能从主项目转维护，并释放 PathwayBridge 的正式实现席位。Release 是本项目交付的一部分，不以“用户自行运行这些命令”代替已授权的发布工作；具体账户信息/凭据确实缺失时才报告阻碍。
