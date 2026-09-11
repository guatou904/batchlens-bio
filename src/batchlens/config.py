"""A bounded, declarative model contract; no formula evaluation."""

from typing import Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from batchlens.sources import Source


class InputError(ValueError):
    """An actionable input problem, distinct from a scientific finding."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Variable(StrictModel):
    role: Literal["target", "batch", "covariate"]
    type: Literal["categorical", "numeric"]
    levels: list[str] | None = None
    reference: str | None = None

    @model_validator(mode="after")
    def validate_type(self) -> Self:
        if self.type == "categorical":
            if not self.levels or len(set(self.levels)) != len(self.levels):
                raise ValueError("Categorical levels must be a nonempty unique list of strings")
            if any(not x.strip() or x != x.strip() for x in self.levels):
                raise ValueError("Levels must be nonempty and have no surrounding whitespace")
            if self.reference not in self.levels:
                raise ValueError("Categorical reference must belong to levels")
        elif self.levels is not None or self.reference is not None:
            raise ValueError("Numeric variables cannot declare levels or reference")
        return self


class Contrast(StrictModel):
    id: str = Field(min_length=1, max_length=200)
    numerator: str
    denominator: str


class StudySpec(StrictModel):
    schema_version: Literal["1.0"]
    design_mode: Literal["independent", "paired"]
    sample_id: str
    unit_id: str
    variables: dict[str, Variable]
    target: str
    adjust_for: list[str]
    contrasts: list[Contrast] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        names = [self.sample_id, self.unit_id, *self.variables]
        if any(not n.strip() or n != n.strip() for n in names):
            raise ValueError("Column names must be nonempty with no surrounding whitespace")
        if self.sample_id == self.unit_id or {self.sample_id, self.unit_id} & self.variables.keys():
            raise ValueError("ID columns and model variables must have distinct names")
        reserved = {"observation_id", "assay_id", "slide_id", "section_id", "cell_type", "region"}
        if {self.sample_id, self.unit_id} & reserved:
            raise ValueError(
                "Sample/unit ID column names cannot reuse optional-table interface names"
            )
        if {"observation_id", "assay_id"} & self.variables.keys():
            raise ValueError("Observation and assay identity columns cannot be model variables")
        target = self.variables.get(self.target)
        if target is None or target.role != "target" or target.type != "categorical":
            raise ValueError("target must name a categorical variable with role target")
        if sum(v.role == "target" for v in self.variables.values()) != 1:
            raise ValueError("Exactly one target variable is supported")
        if len(target.levels or []) < 2:
            raise ValueError("target needs at least two levels")
        if len(set(self.adjust_for)) != len(self.adjust_for):
            raise ValueError("adjust_for must not contain duplicates")
        if set(self.adjust_for) != set(self.variables) - {self.target}:
            raise ValueError(
                "adjust_for must contain every declared non-target variable exactly once"
            )
        if not any(v.role == "batch" for v in self.variables.values()):
            raise ValueError("Declare at least one batch variable")
        if any(v.role == "batch" and v.type != "categorical" for v in self.variables.values()):
            raise ValueError("Batch variables must be categorical in v0.1")
        if self.design_mode == "paired" and len(target.levels or []) != 2:
            raise ValueError("paired mode requires exactly two target levels")
        if len({c.id for c in self.contrasts}) != len(self.contrasts):
            raise ValueError("Contrast IDs must be unique")
        for contrast in self.contrasts:
            if contrast.numerator == contrast.denominator:
                raise ValueError("Contrast numerator and denominator must differ")
            if not {contrast.numerator, contrast.denominator} <= set(target.levels or []):
                raise ValueError("Contrast levels must be declared target levels")
        return self


class UniqueSafeLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently changing the declared design."""


def _mapping(loader: UniqueSafeLoader, node: yaml.MappingNode) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str):
            raise InputError("YAML mapping keys must be strings")
        if key in result:
            raise InputError(f"Duplicate YAML key at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def read_spec(path: Source) -> StudySpec:
    try:
        raw = path.read_text(encoding="utf-8-sig")
        if len(raw) > 1_000_000:
            raise InputError("Design configuration exceeds 1 MB")
        # Aliases are unnecessary here and can create recursive/expanding documents.
        if any(isinstance(t, (yaml.AliasToken, yaml.AnchorToken)) for t in yaml.scan(raw)):
            raise InputError("YAML anchors and aliases are unsupported; use explicit values")
        return StudySpec.model_validate(yaml.load(raw, Loader=UniqueSafeLoader))
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(map(str, e['loc'])) or 'design'}: {e['msg']}"
            for e in exc.errors(include_input=False, include_url=False)
        )
        raise InputError(details) from exc
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise InputError(f"Cannot read design ({type(exc).__name__}); check path and YAML") from exc
