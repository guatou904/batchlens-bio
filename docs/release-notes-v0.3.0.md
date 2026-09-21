# BatchLens Bio 0.3.0 — Unified workbench / 统一工作台

Start with one cell metadata table or an explicit samples/YAML design. Both paths now use the same BatchLens contrast engine.

- **Quick check:** guided column roles, explicit comparison direction and sampling structure, configurable cell-type donor coverage/dominance checks, and conversion to standard advanced inputs.
- **Bilingual delivery:** Chinese/English UI and offline HTML reports; switching language does not rerun the audit. JSON keeps canonical English keys and rule IDs. Each report ZIP includes both languages, tables and hashes.
- **Usability:** evidence panels, responsive layouts, keyboard controls and three original quick-mode synthetic demos. The seven advanced scenarios and CLI remain available.
- **Compatibility:** existing design YAML stays at schema 1.0; optional `cell_coverage` enables the new checks. Output schema/ruleset 1.1 adds `cell_support` and optional quick-input provenance. Quick import accepts CSV/TSV; export h5ad metadata before importing.

Audits run locally and do not read or correct expression data. Raw uploads are not persisted; completed report bundles remain in `~/BatchLens Audits`. `ESTIMABLE` is a model-specific algebraic result, not a power or validity certificate. Unsupported sampling structures remain `NOT_ASSESSED`. External user validation and independent statistical review are still outstanding.

---

可从一份逐细胞元数据表开始，也可使用样本表与 YAML 设计声明。两个入口现在共用同一套 BatchLens 比较审计引擎。

- **快速检查：** 引导确认列含义、比较方向和采样方式，支持细胞类型内的供体覆盖与单供体占比阈值，并可转换为标准高级输入。
- **双语交付：** 中英文界面与离线 HTML 报告；切换语言不重新计算。JSON 保持标准英文键与规则 ID，完整 ZIP 同时包含双语报告、表格和哈希。
- **交互改进：** 证据面板、移动端布局、键盘操作与三个原创快速合成示例；七个高级示例和命令行继续保留。
- **兼容性：** 原设计 YAML 仍使用 1.0 格式，可通过可选 `cell_coverage` 启用新检查。输出格式与规则集升级至 1.1，增加 `cell_support` 和可选的快速输入来源信息。快速导入支持 CSV/TSV；h5ad 需先导出元数据。

审计全程本机运行，不读取或校正表达数据。原始上传文件不持久化，完成的报告包保存在 `~/BatchLens Audits`。`ESTIMABLE` 只表示指定模型下在代数上可估计，不代表功效充足或结论有效；超出支持范围的采样结构仍显示 `NOT_ASSESSED`。外部用户验证与独立统计评审尚未完成。


## Install / 安装

Download the matching macOS DMG or Windows x64 installer from this release, or install with Python 3.12/3.13:

```sh
python -m pip install "batchlens-bio==0.3.0"
batchlens serve
```

选择本页对应系统的安装包，或使用以上命令。Mac 为 ad-hoc 签名，尚未 Developer ID 签名/公证；Windows 尚未 Authenticode 签名。Windows 若缺少 WebView2，初次安装该运行时需联网。

SHA256SUMS covers the attached files. The release workflow URL below records the exact tag's core tests, browser checks and three native builds. PyPI publication/verification runs separately; see the [publication workflow](https://github.com/guatou904/batchlens-bio/actions/workflows/pypi.yml) and [validation record](https://github.com/guatou904/batchlens-bio/blob/main/docs/validation-record.md). Earlier releases are preserved.
