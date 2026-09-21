"""Human-readable translations; canonical scientific JSON is never translated."""

from typing import Any

FINDINGS_ZH = {
    "BL-UNIT-001": (
        "实验单位存在重复取样",
        "核对独立生物学单位及重复采样结构。额外文库或切片不会增加独立实验单位。",
    ),
    "BL-UNIT-002": (
        "条件中的实验单位少于两个",
        "复核生物学重复。该提示不等于样本量或统计功效评估。",
    ),
    "BL-COVER-001": (
        "部分条件与批次组合没有样本",
        "检查分配覆盖；空组合本身不等于指定比较不可估计。",
    ),
    "BL-COVER-002": (
        "部分样本没有关联的细胞或空间点位",
        "确认观测表是否有意只导出部分样本，核对元数据完整性。",
    ),
    "BL-SUPPORT-001": (
        "采样结构超出所声明模型的支持范围",
        "复核实验单位和模型。工具不会自动删除或合并样本；本次比较标记为未评估。",
    ),
    "BL-DESIGN-001": (
        "设计矩阵存在冗余列",
        "检查依赖关系及每个具体比较。矩阵秩亏不等于所有比较不可估计，不要直接删除批次变量。",
    ),
    "BL-NUMERIC-001": ("设计接近奇异，对数值容差敏感", "复核协变量冗余及数值诊断结果。"),
    "BL-CONTRAST-001": (
        "指定比较在当前模型下不可估计",
        "考虑补充交叉分配的样本，或调整科学问题。批次校正无法补回设计中不存在的信息。",
    ),
    "BL-CELL-001": (
        "达到细胞数阈值的供体不足",
        "复核供体覆盖。此计数在每个条件及细胞类型内合并同一供体的样本；阈值是复核提示，不是功效检验。",
    ),
    "BL-CELL-002": ("单个供体占据了较高比例的细胞", "检查采样和供体贡献，不要据此自动删除供体。"),
    "BL-CELL-003": ("该条件未观测到这一细胞类型", "区分生物学缺失、过滤、注释差异与导出遗漏。"),
}


def resolve_evidence(finding: dict[str, Any], result: dict[str, Any]) -> list[Any]:
    values = []
    for pointer in finding["evidence_refs"]:
        value: Any = result
        for part in pointer.strip("/").split("/"):
            key = part.replace("~1", "/").replace("~0", "~")
            value = value[int(key)] if isinstance(value, list) else value[key]
        values.append(value)
    return values


def finding_copy(finding: dict[str, Any], result: dict[str, Any], language: str) -> dict[str, str]:
    if language == "en":
        return {"title": finding["message"], "action": finding["suggested_next_step"]}
    title, action = FINDINGS_ZH.get(
        finding["rule_id"], (finding["message"], finding["suggested_next_step"])
    )
    if finding["rule_id"].startswith("BL-CELL-"):
        row = resolve_evidence(finding, result)[0]
        title += f" · {row['cell_type']} / {row['target_level']}"
    elif finding["rule_id"] == "BL-CONTRAST-001":
        title += f" · {resolve_evidence(finding, result)[0]['id']}"
    elif finding["rule_id"] == "BL-UNIT-002":
        levels = [str(r["target_level"]) for r in result["target_counts"] if r["units"] < 2]
        title += " · " + ", ".join(levels)
    return {"title": title, "action": action}
