# BatchLens Bio

[English](https://github.com/guatou904/batchlens-bio/blob/main/README.md) | [简体中文](https://github.com/guatou904/batchlens-bio/blob/main/README.zh-CN.md)

**面向单细胞与空间组学的实验设计与批次混杂体检工具。**

BatchLens 帮助科研人员在分析数据、解释结果之前，检查一个关键问题：**当前的样本设计，是否支持我们想要进行的生物学比较？**

它根据样本元数据和明确的设计声明，检查实验单位、目标条件与批次的覆盖关系，以及指定比较在加性固定效应模型下是否可估计，生成离线 HTML 报告、JSON 结果和可追溯表格。无需读取表达矩阵或空间图像。

[GitHub Releases](https://github.com/guatou904/batchlens-bio/releases) · [PyPI](https://pypi.org/project/batchlens-bio/) · [网页和桌面版指南](docs/desktop.md)

**0.3.0 统一工作台：** 已将 scDesign Audit 的快速导入、中英文界面和细胞类型供体覆盖检查整合到 BatchLens。两个入口共用同一套计算规则。[迁移与检查范围](docs/quick-check.md) · [实际验证记录](docs/validation-record.md)。

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

## 打开统一工作台

准备 Python 3.12 或 3.13，安装发行版本：

```sh
python -m pip install "batchlens-bio==0.3.0"
batchlens serve
```

源码或开发分支可改用 `python -m pip install .` 安装。

先点 **打开示例报告** 即可体验，无需真实实验数据。界面默认中文，右上角 **EN** 切换英文；已有结果切换语言时不会重新计算。

| 入口 | 准备什么 | 需要确认什么 |
|---|---|---|
| 快速检查 | 每行一个细胞的 CSV/TSV | 样本、供体、条件、批次、细胞类型；比较方向与采样方式 |
| 高级设计 | 样本表 + YAML 设计声明 | 明确比较、分类/数值协变量、独立或配对设计；可添加观测和实验测定关联表 |

快速检查会预览字段，时间点默认不纳入模型。可以设置细胞类型内的供体数、每供体细胞数与单供体占比复核阈值；这些阈值不是功效或有效样本量证明。**转为高级输入** 可生成并下载标准表格和设计文件，不会额外运行审计。[完整输入说明](docs/quick-check.md)。

全程本机处理，无需账户。原始上传文件只在内存中使用，完成的报告包保存在 `~/BatchLens Audits`。可下载中英文 HTML、JSON 或完整 ZIP；关闭应用不会清除已保存报告。

![BatchLens 统一工作台](https://raw.githubusercontent.com/guatou904/batchlens-bio/v0.3.0/docs/workbench-home.png)

快速模式提供三个原创合成示例，高级模式保留七个原有示例。[中文报告示例](docs/quick-demo.zh.html) · [英文报告示例](docs/quick-demo.en.html)。

**桌面版：** 从 [GitHub Releases](https://github.com/guatou904/batchlens-bio/releases) 选择 Apple Silicon Mac、Intel Mac 或 Windows x64 安装包，内含 Python 与依赖。0.3.0 使用统一工作台，0.2.0 保留旧高级界面。安装方式、平台证据和 alpha 签名状态见[桌面指南](docs/desktop.md)。

**命令行仍可使用：**

```sh
batchlens demo --case balanced --out demo-balanced
batchlens demo --case confounded-time --out demo-confounded --language zh --fail-on none
```

第二个示例故意展示完全混杂。`--fail-on none` 只改变退出策略，不隐藏发现。输出目录必须尚不存在、且父目录已存在。

## 检查自己的数据

准备一个每行对应一个样本的 CSV/TSV 文件，以及一份 YAML 设计声明。ID 按字符串处理。请明确声明实验单位，例如受试者或动物，不要默认每个细胞或空间点位都是独立重复。

```sh
batchlens validate --samples samples.tsv --design design.yaml
batchlens audit --samples samples.tsv --design design.yaml --out audit-001
batchlens audit --samples samples.tsv --design design.yaml \
  --observations cells.tsv --assays assays.tsv --out audit-002
```

[输入格式指南](https://github.com/guatou904/batchlens-bio/blob/main/docs/input-schema.md) 提供字段说明和完整配置示例。`--observations` 可补充细胞或空间点位的元数据，用于描述性汇总；`--assays` 可补充样本与实验测定的关联。程序不读取 h5ad、表达矩阵或空间图像。

界面与 HTML 报告支持中文和英文；CLI 支持 `--language zh`，JSON 字段、规则 ID 和标准记录保持英文。

## 如何理解结果？

| 比较状态 | 含义 |
|---|---|
| `ESTIMABLE` | 在声明的模型下，指定比较在代数上可估计；**不代表**统计功效充足、生物学解释正确或因果关系成立 |
| `NON_ESTIMABLE` | 在该模型下，指定比较无法被唯一确定 |
| `NOT_ASSESSED` | 采样结构超出当前支持的独立或配对模型范围；仍会进行描述性检查 |

设计矩阵秩亏不意味着所有比较都不可估计；条件与批次只有部分重叠，也不等于完全混杂。增加细胞或技术切片数量，不会自动增加独立实验单位。详见[统计方法](https://github.com/guatou904/batchlens-bio/blob/main/docs/methods.md)与[结果解释](https://github.com/guatou904/batchlens-bio/blob/main/docs/interpretation.md)。

## 输出与自动化

- `report.html`：所选语言的离线报告；同时附带 `report.en.html` 和 `report.zh.html`。
- `result.json`：输出格式与规则集 1.1；新增供体覆盖和快速导入来源信息。设计 YAML 格式仍为 1.0。
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

BatchLens 当前源码为 v0.3.0，是探索阶段的早期版本，已完成自动化测试和全新环境安装验证，仍需更多真实研究场景的检验。外部用户验证与独立科学评审尚未完成；具体证据与待办事项见[验证记录](https://github.com/guatou904/batchlens-bio/blob/main/docs/validation-record.md)。

欢迎通过 [GitHub Issues](https://github.com/guatou904/batchlens-bio/issues) 提交使用反馈、最小复现案例和统计方法建议。报告安装或科学计算问题时，请注明软件版本，并使用合成数据构造复现案例。后续迭代优先处理问题修复和真实用户反馈。

维护者：[guatou904](https://github.com/guatou904)。
