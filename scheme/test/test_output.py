
import sys
from StringIO import StringIO
from scheme.ssparser import parse
from scheme.execution import ExecutionContext


def capture_output(func):
    s = StringIO()
    so = sys.stdout
    sys.stdout = s
    try:
        func()
    finally:
        sys.stdout = so
    res = s.getvalue()
    s.close()
    return res

def eval_noctx(expr):
    return parse(expr)[0].eval(ExecutionContext())

def test_display():
    tests = [("(display 'foobar)", "foobar"),
             ("(display 42)", "42"),
             ("(display \"Hello World!\")", "Hello World!"),
             ("(display '(1 2 3))", "(1 2 3)"),
             ("(display #\\c)", "c"),
            ]
    for code, expected in tests:
        out = capture_output(lambda: eval_noctx(code))
        assert out == expected

def test_newline():
    out = capture_output(lambda: eval_noctx("(newline)"))
    assert out == "\n"

def test_write():
    tests = [("(write 'foobar)", "foobar"),
             ("(write 42)", "42"),
             ("(write \"Hello World!\")", "\"Hello World!\""),
             ("(write '(1 (0 0) \"Alice\"))", "(1 (0 0) \"Alice\")"),
             ("(write #\\c)", "#\\c"),
            ]
    for code, expected in tests:
        out = capture_output(lambda: eval_noctx(code))
        assert out == expected
