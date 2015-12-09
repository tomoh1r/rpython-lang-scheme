"""
A simple standalone target for the scheme interpreter.
"""

import os
import sys
from rpython.rlib.streamio import open_file_as_stream
from rpython.rlib.parsing.makepackrat import BacktrackException
from scheme.ssparser import parse
from scheme.object import SchemeQuit, ContinuationReturn
from scheme.execution import ExecutionContext

# __________  Entry point  __________


def entry_point(argv):
    if len(argv) == 2:
        path = argv[1]
        try:
            f = open_file_as_stream(path, buffering=0)
        except OSError as e:
            os.write(2, "%s -- %s (LoadError)\n" % (os.strerror(e.errno), path))
            return 1
        try:
            code = f.readall()
        finally:
            f.close()

        try:
            t = parse(code)
        except BacktrackException, e:
            (line, col) = e.error.get_line_column(code)
            #expected = " ".join(e.error.expected)
            os.write(2, "parse error in line %d, column %d" % (line, col))
            return 1

        #this should not be necessary here
        assert isinstance(t, list)
        ctx = ExecutionContext()
        try:
            for sexpr in t:
                print sexpr.to_string()   # for debugging
                try:
                    w_retval = sexpr.eval(ctx)
                    print w_retval.to_string()
                except ContinuationReturn, e:
                    print e.result.to_string()

        except SchemeQuit, e:
            return 0

        return 0
    else:
        print "Usage: %s schemesourcefile" % argv[0]
        return 1

# _____ Define and setup target ___

def target(driver, args):
    driver.exe_name = 'ss-%(backend)s'
    return entry_point, None

if __name__ == '__main__':
    entry_point(sys.argv)
