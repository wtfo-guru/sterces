# sterces

[![Build Status](https://github.com/wtfo-guru/sterces/workflows/Sterces/badge.svg?branch=main&event=push)](https://github.com/wtfo-guru/sterces/actions?query=workflow%3ASterces)
[![codecov](https://codecov.io/gh/wtfo-guru/sterces/branch/main/graph/badge.svg)](https://codecov.io/gh/wtfo-guru/sterces)
[![Python Version](https://img.shields.io/pypi/pyversions/sterces.svg)](https://pypi.org/project/sterces/)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)

## Rationale

I am a retired software engineer. I have a small home lab of less than 10 servers and
workstations. I also manage a very small number of cloud instances. Having a networked
secrets system is not a viable solution for me for several reasons, so I needed a local
secrets tool that could be managed easily via ansible.

Before you mention how insecure this tool is, I must say that it is protected by file
permissions in the home directory of my concierge user account. I take normal
precautions to protect access to this (and other user accounts) so if the concierge or
root account is breached, the contents of my secrets files are the least of my worries.

## Features

- Wrapper functions to allow adding, updating, and looking up data from a keepass database file

- Fully typed with annotations and checked with mypy, [PEP561 compatible](https://www.python.org/dev/peps/pep-0561/)

## Installation

```bash
pip install sterces
```

## Documentation

- [Stable](https://sterces.readthedocs.io/en/stable)

- [Latest](https://sterces.readthedocs.io/en/latest)

## License

[MIT](https://github.com/wtfo-guru/sterces/blob/main/LICENSE)

## Credits

This project uses [`pykeepass`](https://github.com/libkeypass/pykeepass).
This project was tested with [`wemake-python-package`](https://github.com/wemake-services/wemake-python-package).
