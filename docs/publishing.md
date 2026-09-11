# Publication runbook

Published baseline: [GitHub v0.1.0](https://github.com/guatou904/batchlens-bio/releases/tag/v0.1.0) and [PyPI v0.1.0](https://pypi.org/project/batchlens-bio/0.1.0/). GitHub environment `pypi`, Trusted Publisher configuration and official-index installation have been verified. Version 0.2.0 adds desktop installers to the existing release pipeline. Consult [GitHub Releases](https://github.com/guatou904/batchlens-bio/releases) for current published versions and actual run evidence. Do not tag or claim CI success until actual checks pass.

## GitHub

Public repository: [guatou904/batchlens-bio](https://github.com/guatou904/batchlens-bio). Only the isolated BatchLens repository is uploaded, excluding portfolio siblings, virtual environments, local artifacts and downloaded public metadata.

1. Authenticate `gh` with the intended owner using its browser flow. Never put tokens in source files or chat.
2. Create the public repository, push the reviewed commit, then inspect all jobs of the actual `CI` run. Fix failures before tagging.
3. After green CI and release-checklist review, tag the verified commit with `v` plus its package version, then push the new tag. The tag workflow repeats CI, builds and clean-installs packages, builds/tests the three desktop installers, generates the real demo and creates a GitHub Release with SHA256SUMS covering every asset.
4. Record commit, tag, run URL and Release URL in the validation record. Do not overwrite published tags or files; fix releases with a new version.

Local actionlint checks syntax/action usage; it does not prove the workflow runs remotely. PyPI is dispatched separately because service-side configuration is required and a GitHub-token-created release does not automatically trigger a downstream release-event workflow.

## PyPI

Use the official [Trusted Publisher process](https://docs.pypi.org/trusted-publishers/using-a-publisher/) and, for the first release, [pending publisher setup](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

The configured PyPI publisher uses project `batchlens-bio`, owner `guatou904`, repository `batchlens-bio`, workflow `pypi.yml`, environment `pypi`. PyPI account `guatou` owns the project. The service-side setup is complete; no long-lived PyPI token is required. Recheck publisher configuration before future releases.

For future versions, dispatch `pypi.yml` from the reviewed default branch with the new release tag. Do not dispatch v0.1.0 again: it is already published. It downloads the existing release files, verifies SHA256SUMS and uploads those exact wheel/sdist bytes. It then installs the exact version from official PyPI in a new environment and runs a demo outside the checkout. Record the successful run and PyPI URL; inspect installation failure or propagation delay before retrying any publication.

No automatic `skip-existing` or release replacement is used. Investigate partial publication rather than assuming a retry is safe. Completed GitHub publication alone does not complete the PyPI gate.
