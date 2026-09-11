# Contributing

Keep changes within metadata-only experimental-design audits. Show a real task and independently checkable example before adding formats/models. Do not add batch correction or unsupported causal conclusions.

Use Python 3.12/3.13 and `uv sync --locked`. Run Ruff, mypy, pytest; build wheel/sdist and test installation outside the checkout. On macOS, if hidden-file flags prevent loading editable `.pth` files, use `uv sync --no-editable` and `uv run --no-editable ...`; do not alter global Python behavior.

Scientific changes need hand-computable counterexamples and independent expected results. The R oracle is optional locally and required in its CI job. Never silently drop samples or adjust models. Record ambiguous/unsupported inputs.

Issue reports should include versions, command, exit code and minimal synthetic reproducer, without patient IDs, credentials, private paths or unpublished data. Update schema/CLI migration notes, rule IDs and evidence pointers. Generated `docs/design.schema.json` must match the configuration model.

No recursive cleanup commands. Existing outputs are never overwritten. Before publishing, follow the release checklist and distinguish executed evidence from pending user validation, scientific review, remote CI and PyPI publication.
