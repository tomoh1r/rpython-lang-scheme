#! /usr/bin/env python
'''Interactive (untranslatable) version of the pypy scheme interpreter '''
from __future__ import absolute_import

import sys
import os

from rpython.rlib.parsing.makepackrat import BacktrackException

here = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(here, 'lang-scheme'))

from scheme.execution import ExecutionContext
from scheme.object import (
    SchemeException,
    SchemeQuit,
    ContinuationReturn
)
from scheme.ssparser import parse


def main():
    print 'PyPy Scheme interpreter'
    ctx = ExecutionContext()
    to_exec = ''
    cont = False
    while True:
        if cont:
            ps = '.. '
        else:
            ps = '-> '
        sys.stdout.write(ps)

        to_exec += sys.stdin.readline()
        if to_exec == '\n':
            to_exec = ''
        elif _check_parens(to_exec):
            try:
                if to_exec == '':
                    print('')
                    raise SchemeQuit
                print(parse(to_exec)[0].eval(ctx).to_repr())
            except SchemeQuit:
                break
            except ContinuationReturn as exc:
                print(exc.result.to_string())
            except SchemeException as exc:
                print('error: %s' % exc)
            except BacktrackException as exc:
                (line, col) = exc.error.get_line_column(to_exec)
                expected = ' '.join(exc.error.expected)
                print('parse error: in line %s, column %s expected: %s'
                      % (line, col, expected))
            to_exec = ''
            cont = False
        else:
            cont = True


def _check_parens(s):
    return s.count('(') == s.count(')')


if __name__ == '__main__':
    main()
