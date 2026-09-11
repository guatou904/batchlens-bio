# BatchLens Bio

[English](https://github.com/guatou904/batchlens-bio/blob/main/README.md) | [简体中文](https://github.com/guatou904/batchlens-bio/blob/main/README.zh-CN.md)

**面向单细胞与空间组学的实验设计与批次混杂体检工具。**

BatchLens 帮助科研人员在分析数据、解释结果之前，检查一个关键问题：**当前的样本设计，是否支持我们想要进行的生物学比较？**

它根据样本元数据和明确的设计声明，检查实验单位、目标条件与批次的覆盖关系，以及指定比较在加性固定效应模型下是否可估计，生成离线 HTML 报告、JSON 结果和可追溯表格。无需读取表达矩阵或空间图像。

[GitHub Releases](https://github.com/guatou904/batchlens-bio/releases) · [PyPI](https://pypi.org/project/batchlens-bio/) · [网页和桌面版指南](docs/desktop.md)

## 为什么需要 BatchLens？

假设 D0 样本全部在批次 A 处理，D7 样本全部在批次 B 处理，那么时间与批次就发生了完全混杂。在 `time + run` 模型下，无法区分时间效应与批次效应。即使获得更多细胞，或者整合后的嵌入图看起来混合良好，也无法补回实验设计中缺失的信息。

scIB、kBET、LISI 用于整合效果评估，仍然有其用途。BatchLens 检查的是样本设计能否支持指定比较，可作为整合评估之前的设计体检环节。

BatchQC、ExploreModelMatrix 已经提供有价值的混杂与设计诊断。BatchLens 的定位是一个提供命令行、本地网页和桌面界面的工具，将实验单位核对、显式比较、机器可读结果和离线报告串联起来，便于纳入可复现分析流程。它使用已有的线性代数方法，不声称提出新的统计方法。详见[竞品分析](https://github.com/guatou904/batchlens-bio/blob/main/COMPETITOR_ANALYSIS.md)。

## 它能帮你检查什么？

- **重复单位是否声明清楚：** 检查样本与实验单位的对应关系，提示超出当前支持范围的重复采样结构，避免把细胞或切片数量误当成独立实验单位数量。
- **条件与批次是否有覆盖缺口：** 展示不同目标条件与批次的样本、实验单位分布，帮助识别混杂风险。
- **指定比较是否可估计：** 在声明的模型下评估具体比较，并提供设计矩阵相关的数值证据。
- **结果是否方便复核和复现：** 输出离线报告、结构化结果、表格、文件哈希和环境信息，便于团队讨论与流程自动化。

实验单位由分析者声明；软件无法仅凭元数据确认其真实独立性。

## 桌面版：下载后直接使用

从 [GitHub Releases](https://github.com/guatou904/batchlens-bio/releases) 下载对应的安装包：

| 系统 | 下载与使用 |
|---|---|
| Mac（Apple Silicon） | 下载 `macOS-arm64.dmg`，把 **BatchLens Bio.app** 拖入 Applications 后打开 |
| Mac（Intel） | 下载 `macOS-x86_64.dmg`，按相同步骤安装 |
| Windows x64 | 下载 `Windows-x64-Setup.exe`，运行安装程序，从开始菜单打开 |

**无需安装 Python、pip 或虚拟环境。** 打开应用后，拖入 `samples.csv`（或 TSV）和 `design.yaml`，点击 **Run Audit**，直接查看报告。可选的 observations、assays 文件也能添加。

0.2.0 为桌面 alpha 版本：Mac 应用经过 ad-hoc 签名，但尚未取得 Apple Developer ID 签名和公证；Windows 安装包尚未取得 Authenticode 签名，系统可能提示未知发布者。Windows 如缺少 WebView2，安装程序会自动安装，此时首次安装需要联网；后续审计可离线运行。具体平台证据和安装说明见[桌面版指南](docs/desktop.md)。

## 轻量方案：本地网页

已有 Python 3.12 或 3.13 的用户，可安装 0.2.0 或从此仓库源码安装，然后运行：

```sh
python -m pip install batchlens-bio==0.2.0
batchlens serve
```

浏览器自动打开 `http://localhost:<可用端口>/<本次会话密钥>/`。拖入样本表和设计文件，点击 **Run Audit**，完整报告即显示在网页内。也可以先点击 **Run example** 体验七种内置合成数据，下载模板后按研究实际修改。

网页和桌面版都在本机完成分析，不上传到云端。原始输入只在内存中处理；完整报告自动保存到用户主目录下的 **BatchLens Audits**。可点击 **Save HTML** 保存单页报告，或 **Download report bundle** 下载包含 JSON、表格和哈希的 ZIP。关闭界面后，已保存报告仍然保留。

上传文件合计上限为 32 MiB，设计文件上限 1 MB。更多设置见[界面使用指南](docs/desktop.md)。原有命令行仍可使用：

```sh
batchlens demo --case balanced --out demo-balanced
batchlens demo --case confounded-time --out demo-confounded --fail-on none
```

第二个示例故意演示完全混杂，报告显示 `NON_ESTIMABLE`；`--fail-on none` 只改变退出策略，不隐藏发现。其他示例包括 `partial-overlap`、`redundant-nuisance`、`paired`、`spatial-replicates` 和 `mixed-assays`。每次 CLI 输出路径必须是尚不存在的新目录，且父目录已存在。

源码安装：克隆仓库后运行 `python -m pip install .`。

![BatchLens 本地审计界面](https://raw.githubusercontent.com/guatou904/batchlens-bio/v0.2.0/docs/web-ui.png)

[离线报告示例](docs/demo.html) · [公开空间组学元数据示例](docs/public-data.md)

## 检查自己的数据

准备一个每行对应一个样本的 CSV/TSV 文件，以及一份 YAML 设计声明。ID 按字符串处理。请明确声明实验单位，例如受试者或动物，不要默认每个细胞或空间点位都是独立重复。

```sh
batchlens validate --samples samples.tsv --design design.yaml
batchlens audit --samples samples.tsv --design design.yaml --out audit-001
batchlens audit --samples samples.tsv --design design.yaml \
  --observations cells.tsv --assays assays.tsv --out audit-002
```

[输入格式指南](https://github.com/guatou904/batchlens-bio/blob/main/docs/input-schema.md) 提供字段说明和完整配置示例。`--observations` 可补充细胞或空间点位的元数据，用于描述性汇总；`--assays` 可补充样本与实验测定的关联。程序不读取 h5ad、表达矩阵或空间图像。

当前应用界面、CLI 和报告使用英文；本页提供中文使用说明。

## 如何理解结果？

| 比较状态 | 含义 |
|---|---|
| `ESTIMABLE` | 在声明的模型下，指定比较在代数上可估计；**不代表**统计功效充足、生物学解释正确或因果关系成立 |
| `NON_ESTIMABLE` | 在该模型下，指定比较无法被唯一确定 |
| `NOT_ASSESSED` | 采样结构超出当前支持的独立或配对模型范围；仍会进行描述性检查 |

设计矩阵秩亏不意味着所有比较都不可估计；条件与批次只有部分重叠，也不等于完全混杂。增加细胞或技术切片数量，不会自动增加独立实验单位。详见[统计方法](https://github.com/guatou904/batchlens-bio/blob/main/docs/methods.md)与[结果解释](https://github.com/guatou904/batchlens-bio/blob/main/docs/interpretation.md)。

## 输出与自动化

- `report.html`：自包含的离线报告，无需网络或 JavaScript。
- `result.json`：带格式版本的设计声明、检查发现、比较结果和数值证据。
- `tables/*.tsv`：样本及实验单位覆盖表，以及可选的注释汇总。
- `manifest.json`：输入与输出文件的 SHA256 哈希、运行环境和依赖版本。
- `COMPLETE`：最后写入的完成标记；缺失表示输出包尚未完整生成。

输出中的 ID 会替换为局部别名，但类别标签和设计取值仍可能包含可识别信息。分享前请检查**所有输出**。程序不导出原始 ID 映射、输入文件绝对路径或逐细胞记录。TSV 中类似电子表格公式的标签会加上前置单引号；JSON 保留原始科学标签。

退出码：`0` 表示完成，`1` 表示内部错误，`2` 表示输入或输出错误，`3` 表示检查发现触发失败策略。默认策略为 `--fail-on critical`。严格的 CI 流程可使用 `--fail-on warning`，让超出模型支持范围等警告也触发失败。`--fail-on none` 仅改变退出行为，不改变结果。`validate` 成功只表示通过输入验证，不表示比较可估计。

## 当前支持范围

独立设计要求每个声明的实验单位恰好对应一个样本。配对设计要求每个实验单位在两个目标水平下各有一个样本，并加入实验单位固定效应。支持分类目标变量，以及加性分类或数值调整变量。

跨多个批次的样本和更复杂的重复采样结构会得到 `NOT_ASSESSED`，不会被静默合并。目前不提供交互项、混合效应推断、功效分析、因果推断、空间相关性检验或批次校正。

仅凭元数据无法确认随机化、独立性或未测量混杂。分析者需要提供符合研究实际的设计声明；接近奇异的设计需要进一步数值复核。当前资源保护上限为 100,000 个样本和 256 个编码后的设计矩阵列，这不是性能保证。

## 开发与验证

```sh
uv sync --locked --no-editable
uv run --no-editable pytest
uv run --no-editable ruff check .
uv run --no-editable mypy
uv run --no-editable python -m build
uv run --no-editable twine check dist/*.whl dist/*.tar.gz
```

[验证记录](https://github.com/guatou904/batchlens-bio/blob/main/docs/validation-record.md) 区分了已完成的测试与尚待补充的外部证据。部分科学测试用例通过 R 的 `model.matrix` 和 QR 分解进行独立实现交叉核对，见 `scripts/verify_r_oracle.R`；这不等同于独立专家评审。CI 与发布流程还检查自动化测试、源码目录之外的安装和演示输出，远程 CI 结果附有实际运行链接。

详见[贡献指南](https://github.com/guatou904/batchlens-bio/blob/main/CONTRIBUTING.md)、[引用信息](https://github.com/guatou904/batchlens-bio/blob/main/CITATION.cff)、[发布检查清单](https://github.com/guatou904/batchlens-bio/blob/main/RELEASE_CHECKLIST.md)和[更新日志](https://github.com/guatou904/batchlens-bio/blob/main/CHANGELOG.md)。代码与合成示例采用 MIT 许可证；公开数据集各自遵循其来源和使用条款。

## 项目状态与反馈

BatchLens 当前源码为 v0.2.0，是探索阶段的早期版本，已完成自动化测试和全新环境安装验证，仍需更多真实研究场景的检验。外部用户验证与独立科学评审尚未完成；具体证据与待办事项见[验证记录](https://github.com/guatou904/batchlens-bio/blob/main/docs/validation-record.md)。

欢迎通过 [GitHub Issues](https://github.com/guatou904/batchlens-bio/issues) 提交使用反馈、最小复现案例和统计方法建议。报告安装或科学计算问题时，请注明软件版本，并使用合成数据构造复现案例。后续迭代优先处理问题修复和真实用户反馈。

维护者：[guatou904](https://github.com/guatou904)。
