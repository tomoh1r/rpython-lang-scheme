'''A simple standalone target for the scheme interpreter.'''
from __future__ import absolute_import

import os
import sys

from rpython.rlib.parsing.makepackrat import BacktrackException
from rpython.rlib.streamio import open_file_as_stream

from scheme.execution import ExecutionContext
from scheme.object import SchemeQuit, ContinuationReturn
from scheme.ssparser import parse


_EXE_NAME = 'scheme-c'


def entry_point(argv):
    path = argv[0] if len(argv) == 1 else argv[-1]
    try:
        f = open_file_as_stream(path, buffering=0)
    except OSError as exc:
        os.write(
            2,
            '%s -- %s (LoadError)\n' % (os.strerror(exc.errno), path))
        return 1

    try:
        code = f.readall()
    finally:
        f.close()

    try:
        t = parse(code)
    except BacktrackException as exc:
        (line, col) = exc.error.get_line_column(code)
        # expected = ' '.join(exc.error.expected)
        os.write(
            2,
            'parse error in line %d, column %d' % (line, col))
        return 1

    ctx = ExecutionContext()
    try:
        for sexpr in t:
            try:
                print(sexpr.eval(ctx).to_string())
            except ContinuationReturn as exc:
                print(exc.result.to_string())
    except SchemeQuit:
        return 0
    else:
        return 0


def target(driver, args):
    driver.exe_name = _EXE_NAME
    return entry_point, None


if __name__ == '__main__':
    entry_point(sys.argv)
