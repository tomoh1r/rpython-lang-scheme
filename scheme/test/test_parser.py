import py
from scheme.ssparser import parse
from scheme.object import W_Boolean, W_Real, W_Integer, W_String
from scheme.object import W_Pair, W_Nil, W_Symbol, W_Character, W_Vector
from scheme.object import SchemeSyntaxError
from rpython.rlib.parsing.makepackrat import BacktrackException

def parse_sexpr(expr):
    return parse(expr)[0]

def unwrap(w_obj):
    """for testing purposes: unwrap a scheme object into a python object"""
    if isinstance(w_obj, W_Real):
        return w_obj.to_number()
    elif isinstance(w_obj, W_Integer):
        return w_obj.to_number()
    elif isinstance(w_obj, W_String):
        return w_obj.strval
    elif isinstance(w_obj, W_Symbol):
        return w_obj.name
    elif isinstance(w_obj, W_Character):
        return w_obj.chrval
    elif isinstance(w_obj, W_Boolean):
        return w_obj.to_boolean()
    elif isinstance(w_obj, W_Pair):
        result = []
        while not isinstance(w_obj, W_Nil):
            result.append(unwrap(w_obj.car))
            w_obj = w_obj.cdr
        return result
    raise NotImplementedError("don't know what to do with: %s" % (w_obj, ))

def test_simple():
    w_fixnum = parse_sexpr('1')
    assert isinstance(w_fixnum, W_Integer)
    assert unwrap(w_fixnum) == 1
    w_fixnum = parse_sexpr('0')
    assert unwrap(w_fixnum) == 0
    assert isinstance(w_fixnum, W_Integer)
    w_fixnum = parse_sexpr('1123')
    assert unwrap(w_fixnum) == 1123
    assert isinstance(w_fixnum, W_Integer)
    w_char = parse_sexpr('#\\a')
    assert isinstance(w_char, W_Character)
    assert unwrap(w_char) == 'a'

def test_symbol():
    w_sym = parse_sexpr('abfa__')
    assert isinstance(w_sym, W_Symbol)
    assert w_sym.to_string() == 'abfa__'
    
    more_syms = ['abc',
                 'call/cc',
                 '+',
                 '-',
                 'set!',
                 'eqv?',
                 'foo.bar',
                ]
    for s in more_syms:
        w_sym = parse_sexpr(s)
        assert isinstance(w_sym, W_Symbol)
        assert w_sym.to_string() == s

def test_string():
    t = parse_sexpr(r'''"don't believe \"them\""''')
    assert isinstance(t, W_String)
    assert unwrap(t) == 'don\'t believe "them"'

    more_strings = [(r'''"simple string"''', r'''simple string'''),
                    (r'''"\\ backslash"''', r'''\ backslash'''),
                    (r'''"\\\\"''',r'''\\'''),
                    (r'''"with \"quotes\""''', r'''with "quotes"'''),
                   ]
    for code, contents in more_strings:
        w_string = parse_sexpr(code)
        assert isinstance(w_string, W_String)
        assert unwrap(w_string) == contents

def test_character():
    w_char = parse_sexpr(r'#\c')
    assert isinstance(w_char, W_Character)
    assert unwrap(w_char) == 'c'

    more_chars = [(r'#\Z', 'Z'),
                  (r'#\,', ','),
                  (r'#\;', ';'),
                  (r'#\)', ')'),
                  (r'#\(', '('),
                  (r'#\#', '#'),
                  (r'#\ ', ' '),
                  (r'#\space', ' '),
                  (r'#\newline', '\n'),
                 ]
     
    for code, result in more_chars:
        w_char = parse_sexpr(code)
        assert isinstance(w_char, W_Character)
        assert unwrap(w_char) == result

    py.test.raises(SchemeSyntaxError, parse_sexpr, r'#\foobar')

def test_objects():
    w_fixnum = parse_sexpr('-12345')
    assert isinstance(w_fixnum, W_Integer)
    assert unwrap(w_fixnum) == -12345

    w_float = parse_sexpr('123456.1234')
    assert isinstance(w_float, W_Real)
    assert unwrap(w_float) == 123456.1234
    w_float = parse_sexpr('-123456.1234')
    assert isinstance(w_float, W_Real)
    assert unwrap(w_float) == -123456.1234

    w_float = parse_sexpr('.1234')
    assert isinstance(w_float, W_Real)
    assert unwrap(w_float) == 0.1234
    w_float = parse_sexpr('12.')
    assert isinstance(w_float, W_Real)
    assert unwrap(w_float) == 12.0

    py.test.raises(BacktrackException, parse_sexpr, '.')

def test_sexpr():
    w_list = parse_sexpr('( 1 )')
    assert isinstance(w_list, W_Pair)
    assert isinstance(w_list.car, W_Integer)
    assert isinstance(w_list.cdr, W_Nil)

    #w_list = parse_sexpr('()')
    #assert isinstance(w_list, W_Nil)

    w_list = parse_sexpr('(+ 1 2)')
    assert isinstance(w_list, W_Pair)
    assert isinstance(w_list.car, W_Symbol)
    assert isinstance(w_list.cdr, W_Pair)
    assert isinstance(w_list.cdr.car, W_Integer)
    assert isinstance(w_list.cdr.cdr.car, W_Integer)
    assert isinstance(w_list.cdr.cdr.cdr, W_Nil)

def test_complex_sexpr():
    #parse more complex sexpr
    t = parse_sexpr(r'''
        (define (fac n) ; comment
            (if (< n 2) n
                (* (fac (- n 1)) n)))
        ''')
    assert isinstance(t, W_Pair)
    assert unwrap(t) == ['define', ['fac', 'n'],
                            ['if', ['<', 'n', 2], 'n',
                                   ['*', ['fac', ['-', 'n', 1]], 'n']]]

def test_ident_gen():
    ch_list = "+-*/azAZ<=>-_~!$%&:?^"
    for char in ch_list:
        yield check_ident_ch, char

def check_ident_ch(char):
    t = parse_sexpr("(" + char + ")")
    assert isinstance(t, W_Pair)
    assert isinstance(t.car, W_Symbol)
    assert unwrap(t.car) == char.lower()
    assert isinstance(t.cdr, W_Nil)

def test_truth_values():
    t = parse_sexpr("#f")
    assert unwrap(t) == False
    t = parse_sexpr("#t")
    assert unwrap(t) == True

def test_list_dotted():
    t = parse_sexpr("(1 . 2)")
    assert isinstance(t, W_Pair)
    assert unwrap(t.car) == 1
    assert unwrap(t.cdr) == 2

    t = parse_sexpr("(1 . (2 . 3))")
    assert unwrap(t.car) == 1
    assert unwrap(t.cdr.car) == 2
    assert unwrap(t.cdr.cdr) == 3

    t = parse_sexpr("(1 . (2 . (3 . ())))")
    assert unwrap(t) == [1, 2, 3]

def test_list_mixed():
    t = parse_sexpr("(1 2 . 3)")
    assert unwrap(t.car) == 1
    assert unwrap(t.cdr.car) == 2
    assert unwrap(t.cdr.cdr) == 3

    t = parse_sexpr("(1 2 . (3 4))")
    assert unwrap(t) == [1, 2, 3, 4]

def test_quote():
    t = parse_sexpr("'a")
    assert unwrap(t) == ['quote', 'a']

    t = parse_sexpr("'(1 '2 3)")
    assert unwrap(t) == ['quote', [1, ['quote', 2], 3]]

def test_qq():
    t = parse_sexpr("`a")
    assert unwrap(t) == ['quasiquote', 'a']

    t = parse_sexpr("`(1 `2 3)")
    assert unwrap(t) == ['quasiquote', [1, ['quasiquote', 2], 3]]

def test_unquote():
    t = parse_sexpr(",a")
    assert unwrap(t) == ['unquote', 'a']

    t = parse_sexpr(",(1 ,2 3)")
    assert unwrap(t) == ['unquote', [1, ['unquote', 2], 3]]

def test_unquote_splicing():
    t = parse_sexpr(",@a")
    assert unwrap(t) == ['unquote-splicing', 'a']

    t = parse_sexpr(",@(list ,@b 3)")
    assert unwrap(t) == ['unquote-splicing', ['list',
                                ['unquote-splicing', 'b'], 3]]

def test_ellipsis():
    w_float = parse_sexpr('...')
    assert isinstance(w_float, W_Symbol)
    assert unwrap(w_float) == "..."

def test_vector():
    w_vect = parse_sexpr('#()')
    assert isinstance(w_vect, W_Vector)
    assert w_vect.get_len() == 0
    assert w_vect.to_repr() == '#()'

    w_vect = parse_sexpr('#(1 2 symb "string")')
    assert isinstance(w_vect, W_Vector)
    assert w_vect.get_len() == 4
    assert w_vect.to_repr() == '#(1 2 symb "string")'

    w_item0 = w_vect.get_item(0)
    assert isinstance(w_item0, W_Integer)
    assert w_item0.to_fixnum() == 1

    w_item2 = w_vect.get_item(2)
    assert isinstance(w_item2, W_Symbol)
    assert w_item2.to_string() == "symb"
