# pypy-lang-scheme

fork from [lang-scheme](https://bitbucket.org/pypy/lang-scheme)

## Quick Start

Build

```console
$ virtualenv --clear --no-setuptools venv
$ ./venv/bin/python misc/get-pip.py
$ ./venv/bin/pip install -U -r requirements.txt
$ ./venv/bin/rpython targetscheme.py
```

, and Run

```console
$ ./scheme-c
hello, world
```
