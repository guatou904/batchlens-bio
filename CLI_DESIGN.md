# BatchLens — CLI design

> 2026-09-12 状态更新：用户已授权完成首个项目并创建/上传仓库；受限 MVP 已实现，本地验证通过，远程发布待认证。以下保留规划背景；当前行为以 README、docs/input-schema.md、docs/methods.md 和 docs/decisions.md 为准。外部 G0/G1 验证并未完成。

2026-09-12；validate / audit / demo 已实现。命令行输入路径相对调用目录解析；设计 YAML 不包含输入文件路径。

## 命令面

```sh
batchlens --version
batchlens validate --samples samples.tsv --design design.yaml
batchlens audit --samples samples.tsv --design design.yaml --out audit-001
batchlens audit --samples samples.tsv --design design.yaml --observations cells.tsv --assays assay-links.tsv --out audit-002
batchlens demo --case confounded-time --out demo-confounded
batchlens demo --case balanced --out demo-balanced
```

只保留 validate / audit / demo；不加入 integrate、correct、recommend-method、auto-fix。demo 运行随包附带的 synthetic metadata，并走与 audit 相同的路径。正常输出摘要到 stdout，进度和错误到 stderr；主要机器接口是输出目录中的 JSON，避免终端文本成为 API。

## 样本与配置示例

以下独立设计有四个独立实验单位，D0/D7 与 run 完全混杂；数字仅为说明契约的 synthetic 示例。

```text
sample_id  unit_id  time  run
s1         u1       D0    A
s2         u2       D0    A
s3         u3       D7    B
s4         u4       D7    B
```

实际输入须为 CSV 或制表符分隔 TSV；上表的对齐空格不是文件分隔约定。

```yaml
schema_version: "1.0"
design_mode: independent
sample_id: sample_id
unit_id: unit_id
variables:
  time:
    role: target
    type: categorical
    levels: [D0, D7]
    reference: D0
  run:
    role: batch
    type: categorical
    levels: [A, B]
    reference: A
target: time
adjust_for: [run]
contrasts:
  - id: D7_vs_D0
    numerator: D7
    denominator: D0
```

固定截距隐含于受限加性模型，报告明确展示 `1 + time + run`。role 为 batch 的变量必须出现在 adjust_for；不得省略已声明技术因素而悄悄发“通过”。用户可以明确更改其声明，但报告必须反映改后的目标和限制。

paired 模式：同一 unit 在两个 target 水平各一行，`design_mode: paired`；unit block 自动作为该模式的公开契约加入并显示。缺配对、每个 unit×target 多个样本、多个配对因子仅给描述检查与 NOT_ASSESSED，不自动删除样本。

## 终端摘要草图

```text
BatchLens audit completed
Experimental units: 4; samples: 4
Declared model: 1 + time + run
D7_vs_D0: NON_ESTIMABLE
Evidence: time[D7] and run[B] are identical design columns.
Scope: the requested time effect cannot be separated from run in this model.
Report: demo-confounded/report.html
JSON: demo-confounded/result.json
```

用语限定在“指定模型的比较”；不说“数据废了”，也不建议直接删除 run 后继续声称控制了批次。

## 错误和 CI 契约

`--fail-on critical|warning|none`，audit/demo 默认 `critical`；配置错误总失败。报告完成后才根据科学 finding 决定退出码，使 CI 失败仍能保留 artifact。

| 退出码 | 含义 |
|---|---|
| 0 | 执行完成，没有达到 --fail-on 的 finding；不代表科学有效 |
| 1 | 非预期内部执行失败；错误不应伪装成 finding |
| 2 | 参数、输入、schema 或输出路径错误 |
| 3 | 报告成功生成，但至少一项达到 --fail-on 阈值 |

NON_ESTIMABLE 对应 critical；NOT_ASSESSED 对应 warning。严格流水线使用 `--fail-on warning`，避免把未评估误当通过。`--fail-on none` 只改变退出行为，不删除 findings。validate 成功也不表示比较可估计。

`--out` 已存在即拒绝（包括空目录），要求父目录已存在；不设计 `--force` 自动删除旧结果。输入路径和异常中的敏感值控制在本地错误日志；共享 HTML 不含默认绝对路径。

## 文档与兼容性

CLI 示例是发布 DoD 的可执行验收脚本来源；`--help` 包含 required columns、退出码、输出文件和限制链接。配置 schema 与输出 schema 独立版本化；新增字段可兼容，改变含义必须记录迁移。首版错误提示英文以便 GitHub issue 复现，提供中文解释指南；不把国际化框架加入 MVP。
