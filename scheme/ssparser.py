from __future__ import absolute_import

from rpython.rlib.parsing.pypackrat import PackratParser
from rpython.rlib.parsing.makepackrat import BacktrackException, Status

from scheme.object import (
    W_Pair, W_Integer, W_String, symbol,
    w_nil, W_Boolean, W_Real,
    w_ellipsis, W_Character, SchemeSyntaxError, W_Vector
)


def str_unquote(s):
    str_lst = []
    pos = 1
    last = len(s)-1
    while pos < last:
        ch = s[pos]
        if ch == '\\':
            pos += 1
            ch = s[pos]
            if ch == '\\' or ch == '\"':
                str_lst.append(ch)
            else:
                raise SchemeSyntaxError
        else:
            str_lst.append(ch)

        pos += 1

    return ''.join(str_lst)

class SchemeParser(PackratParser):
    r"""
    STRING:
        c = `\"([^\\\"]|\\\"|\\\\)*\"`
        IGNORE*
        return {W_String(str_unquote(c))};

    CHARACTER:
        c = `#\\(.|[A-Za-z]+)`
        IGNORE*
        return {W_Character(c[2:])};

    SYMBOL:
        c = `[\+\-\*\^\?a-zA-Z!<=>_~/$%&:][\+\-\*\^\?a-zA-Z0-9!<=>_~/$%&:.]*`
        IGNORE*
        return {symbol(c)};

    ELLIPSIS:
        c = '...'
        IGNORE*
        return {w_ellipsis};

    FIXNUM:
        c = `\-?(0|([1-9][0-9]*))`
        IGNORE*
        return {W_Integer(int(c))};

    FLOAT:
        c = `\-?([0-9]*\.[0-9]+|[0-9]+\.[0-9]*)`
        IGNORE*
        return {W_Real(float(c))};

    BOOLEAN:
        c = `#(t|f)`
        IGNORE*
        return {W_Boolean(c[1] == 't')};

    IGNORE:
        ` |\n|\t|;[^\n]*`;
    
    EOF:
        !__any__;
    
    file:
        IGNORE*
        s = sexpr*
        EOF
        return {s};
    
    quote:
       `'`
       s = sexpr
       return {quote(s)};
    
    qq:
       `\``
       s = sexpr
       return {qq(s)};
       
       
    unquote_splicing:
       `\,@`
       s = sexpr
       return {unquote_splicing(s)};

    unquote:
       `\,`
       s = sexpr
       return {unquote(s)};
    
    sexpr:
        list
      | vector  
      | quote
      | qq
      | unquote_splicing
      | unquote
      | ELLIPSIS
      | FLOAT
      | FIXNUM
      | BOOLEAN
      | SYMBOL
      | CHARACTER
      | STRING;

    list:
        '('
        IGNORE*
        p = pair
        ')'
        IGNORE*
        return {p};

    vector:
        '#('
        IGNORE*
        v = sexpr*
        ')'
        IGNORE*
        return {W_Vector(v)};

    pair:
        car = sexpr
        '.'
        IGNORE*
        cdr = sexpr
        return {W_Pair(car, cdr)}
      | car = sexpr
        cdr = pair
        return {W_Pair(car, cdr)}
      | return {w_nil};
    """

def parse(code):
    p = SchemeParser(code)
    return p.file()

##
# Parser helpers
##
def quote(sexpr):
    return W_Pair(symbol('quote'), W_Pair(sexpr, w_nil))

def qq(sexpr):
    return W_Pair(symbol('quasiquote'), W_Pair(sexpr, w_nil))

def unquote(sexpr):
    return W_Pair(symbol('unquote'), W_Pair(sexpr, w_nil))

def unquote_splicing(sexpr):
    return W_Pair(symbol('unquote-splicing'), W_Pair(sexpr, w_nil))
