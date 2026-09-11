BatchLens Bio 0.1.0 is an exploratory, metadata-only experimental-design audit tool.

It checks experimental units, sample/batch coverage and explicit additive-model contrasts, with independent/paired support boundaries. Outputs include an offline HTML report, versioned JSON findings, tables and hashed provenance. Seven synthetic demos ship in the package.

Download the wheel or source archive and install with `python -m pip install <downloaded-file>`. Run `batchlens demo --case confounded-time --out demo --fail-on none`, then open `demo/report.html`. The attached HTML is a real synthetic demo output; SHA256SUMS covers the release files.

Limitations: no expression correction, power or causal inference, spatial correlation test, interaction/random-effect model, or guarantee of scientific validity. External user validation and independent scientific review remain pending. Python 3.12/3.13 are the CI targets; platform support should be assessed using the attached successful workflow evidence.

See README, methods, input schema and validation record. GitHub release does not imply PyPI publication; the latter is tracked separately.
