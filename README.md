# NCTL
Fuses ngrok and CloudFront offering a fully automated solution

![Python][label-pyversion]

**Platform Supported**

![Platform][label-platform]

**Deployments**

[![pages][label-actions-pages]][gha_pages]
[![pypi][label-actions-pypi]][gha_pypi]
[![markdown][label-actions-markdown]][gha_md_valid]

[![Pypi][label-pypi]][pypi]
[![Pypi-format][label-pypi-format]][pypi-files]
[![Pypi-status][label-pypi-status]][pypi]

## Kick off

**Recommendations**

- Install `python` [3.10] or [3.11]
- Use a dedicated [virtual environment]

**Install nctl**
```shell
python -m pip install nctl
```

**Initiate - IDE**
```python
import nctl


if __name__ == '__main__':
    nctl.tunnel()
```

**Initiate - CLI**
```shell
nctl start
```

> Use `nctl --help` for usage instructions.

## Environment Variables

<details>
<summary><strong>Sourcing environment variables from an env file</strong></summary>

> _By default, `nctl` will look for a `.env` file in the current working directory._<br>
> Refer [samples] directory for examples.

</details>

- **PORT** - Port number to expose using ngrok.
- **HOST** - Hostname of the server that has to be exposed.
- **NGROK_AUTH** - Auth token for ngrok.
- **NGROK_CONFIG** - Ngrok configuration filepath. Auto-created when auth token is specified.
- **DISTRIBUTION_ID** - Cloudfront distribution ID. Required to update an existing distribution.
- **DISTRIBUTION_CONFIG** - Cloudfront distribution config filepath. Required to create a new distribution.
- **DEBUG** - Boolean flag to enable debug level logging.

#### AWS Config

- **AWS_PROFILE_NAME** - AWS profile name.
- **AWS_ACCESS_KEY_ID** - AWS access key ID.
- **AWS_SECRET_ACCESS_KEY** - AWS secret key.
- **AWS_REGION_NAME** - AWS region name.

## Coding Standards
Docstring format: [`Google`][google-docs] <br>
Styling conventions: [`PEP 8`][pep8] and [`isort`][isort]

## [Release Notes][release-notes]
**Requirement**
```shell
python -m pip install gitverse
```

**Usage**
```shell
gitverse-release reverse -f release_notes.rst -t 'Release Notes'
```

## Linting
`pre-commit` will ensure linting, run pytest, generate runbook & release notes, and validate hyperlinks in ALL
markdown files (including Wiki pages)

**Requirement**
```shell
python -m pip install sphinx==5.1.1 pre-commit recommonmark
```

**Usage**
```shell
pre-commit run --all-files
```

## Pypi Package
[![pypi-module][label-pypi-package]][pypi-repo]

[https://pypi.org/project/nctl/][pypi]

## Runbook
[![made-with-sphinx-doc][label-sphinx-doc]][sphinx]

[https://thevickypedia.github.io/nctl/][runbook]

## License & copyright

&copy; Vignesh Rao

Licensed under the [MIT License][license]

[//]: # (Labels)

[label-actions-markdown]: https://github.com/thevickypedia/nctl/actions/workflows/markdown.yaml/badge.svg
[label-pypi-package]: https://img.shields.io/badge/Pypi%20Package-nctl-blue?style=for-the-badge&logo=Python
[label-sphinx-doc]: https://img.shields.io/badge/Made%20with-Sphinx-blue?style=for-the-badge&logo=Sphinx
[label-pyversion]: https://img.shields.io/badge/python-3.10%20%7C%203.11-blue
[label-platform]: https://img.shields.io/badge/Platform-Linux|macOS|Windows-1f425f.svg
[label-actions-pages]: https://github.com/thevickypedia/nctl/actions/workflows/pages/pages-build-deployment/badge.svg
[label-actions-pypi]: https://github.com/thevickypedia/nctl/actions/workflows/python-publish.yaml/badge.svg
[label-pypi]: https://img.shields.io/pypi/v/nctl
[label-pypi-format]: https://img.shields.io/pypi/format/nctl
[label-pypi-status]: https://img.shields.io/pypi/status/nctl

[3.10]: https://docs.python.org/3/whatsnew/3.10.html
[3.11]: https://docs.python.org/3/whatsnew/3.11.html
[virtual environment]: https://docs.python.org/3/tutorial/venv.html
[release-notes]: https://github.com/thevickypedia/nctl/blob/master/release_notes.rst
[gha_pages]: https://github.com/thevickypedia/nctl/actions/workflows/pages/pages-build-deployment
[gha_pypi]: https://github.com/thevickypedia/nctl/actions/workflows/python-publish.yaml
[gha_md_valid]: https://github.com/thevickypedia/nctl/actions/workflows/markdown.yaml
[google-docs]: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
[pep8]: https://www.python.org/dev/peps/pep-0008/
[isort]: https://pycqa.github.io/isort/
[sphinx]: https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html
[pypi]: https://pypi.org/project/nctl
[pypi-files]: https://pypi.org/project/nctl/#files
[pypi-repo]: https://packaging.python.org/tutorials/packaging-projects/
[license]: https://github.com/thevickypedia/nctl/blob/master/LICENSE
[runbook]: https://thevickypedia.github.io/nctl/
