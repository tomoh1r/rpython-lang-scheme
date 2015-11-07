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

and Run

```console
$ ./scheme-c sample.ss
<<W_Boolean object at 0x7f61f0e7a020>>
<<W_Boolean object at 0x7f61f0e7a020>>
```
