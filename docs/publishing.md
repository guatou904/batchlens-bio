# Publication runbook

Current state: local candidate only. Repository creation/upload is authorized; GitHub CLI authentication is missing. PyPI account/Trusted Publisher configuration has not been established. Do not tag a release or claim remote CI success until actual checks pass.

## GitHub

The intended public repository is `guatou904/batchlens-bio`. Check availability again before creation; no repository is claimed to exist yet. Only the isolated BatchLens repository is uploaded, excluding portfolio siblings, virtual environments, local artifacts and downloaded public metadata.

1. Authenticate `gh` with the intended owner using its browser flow. Never put tokens in source files or chat.
2. Create the public repository, push the reviewed commit, then inspect all jobs of the actual `CI` run. Fix failures before tagging.
3. After green CI and release-checklist review, tag the verified commit `v0.1.0` and push the tag. The tag workflow repeats CI, builds and clean-installs packages, generates the real demo and creates a GitHub Release with SHA256SUMS.
4. Record commit, tag, run URL and Release URL in the validation record. Do not overwrite published tags or files; fix releases with a new version.

Local actionlint checks syntax/action usage; it does not prove the workflow runs remotely. PyPI is dispatched separately because service-side configuration is required and a GitHub-token-created release does not automatically trigger a downstream release-event workflow.

## PyPI

Use the official [Trusted Publisher process](https://docs.pypi.org/trusted-publishers/using-a-publisher/) and, for the first release, [pending publisher setup](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

Configure the PyPI publisher with project `batchlens-bio`, owner `guatou904`, repository `batchlens-bio`, workflow `pypi.yml`, environment `pypi`. The account owner must complete this service-side setup; no long-lived PyPI token is required by the prepared workflow. Availability and account configuration must be verified before publishing.

Dispatch `pypi.yml` from the reviewed default branch with tag `v0.1.0`. It downloads the existing release files, verifies SHA256SUMS and uploads those exact wheel/sdist bytes. It then installs the exact version from official PyPI in a new environment and runs a demo outside the checkout. Record the successful run and PyPI URL; inspect installation failure or propagation delay before retrying any publication.

No automatic `skip-existing` or release replacement is used. Investigate partial publication rather than assuming a retry is safe. Completed GitHub publication alone does not complete the PyPI gate.
