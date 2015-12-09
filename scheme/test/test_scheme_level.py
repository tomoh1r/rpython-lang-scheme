import py
from scheme.ssparser import parse
from scheme.execution import ExecutionContext
from scheme.object import *
import re

# A scheme level macro, which raises an AssertionError at python
# level. This python level Errors are then reported by pytest.py

class Assert(W_Macro):
    def call(self, ctx, lst):
        if not isinstance(lst, W_Pair):
            raise SchemeSyntaxError
        w_test = lst.car
        if lst.cdr is w_nil:
            comment = w_test.to_string()
        else:
            w_rest = lst.get_cdr_as_pair()
            if w_rest.cdr is not w_nil:
                raise WrongArgsNumber
            comment = w_rest.car.to_string()

        if isinstance(w_test, W_Pair) and isinstance(w_test.car, W_Symbol):
            w_test_oper = w_test.car
            test_name = w_test_oper.name
            if test_name in ['eq?', 'eqv?', 'equal?']:
                w_iter = w_test.cdr
                if not isinstance(w_iter, W_Pair):
                    raise SchemeSyntaxError
                w_first = w_iter.car
                w_iter = w_iter.cdr
                if not isinstance(w_iter, W_Pair):
                    raise SchemeSyntaxError
                w_second = w_iter.car
                w_iter = w_iter.cdr
                if not w_iter is w_nil:
                    raise WrongArgsNumber

                w_got = w_first.eval(ctx)
                w_expected= w_second.eval(ctx)

                comment += "\n + got: " + w_got.to_repr()
                comment += "\n + expected: " + w_expected.to_repr()

                w_compare = ctx.get(test_name)
                if not isinstance(w_compare, W_Procedure):
                    raise SchemeSyntaxError
                w_test_result = w_compare.procedure(ctx,
                    [w_got, w_expected])
            else:
                w_test_result = w_test.eval(ctx)
        else:
            w_test_result = w_test.eval(ctx)

        assert w_test_result.to_boolean(), comment

        return w_undefined

w_assert = Assert("assert")

def run_with_assert(text):
    ctx = ExecutionContext()
    ctx.set("assert", w_assert)
    
    for stmt in parse(text):
        w_result = stmt.eval(ctx)

    return w_result

def test_assert():
    run_with_assert(r'(assert #t "No fail for passed assert")')
    run_with_assert(r'(assert (or #f #t))')
    py.test.raises(AssertionError, run_with_assert,
        r'(assert #f "Failed assert raises")')
    py.test.raises(AssertionError, run_with_assert,
        r'(define foo #f) (+ 1 1) (assert foo "more complex test")')
    e = py.test.raises(AssertionError, run_with_assert,
        r'(assert (eqv? (+ 9 7) 10))')
    assert re.search('got: \d+', str(e.value))
    assert re.search('expected: 10', str(e.value))

def test_simple():
    run_with_assert(r"""
(assert (equal? (list 1 2 3) '(1 2 3)))
(assert (equal? (cons 'a 'b) '(a . b)))
(assert (eq? (car (cons 'a 'b)) 'a))
(assert (eq? (cdr (cons 'a 'b)) 'b))
(assert (eqv? (+ 1 2) 3))
(assert (eqv? (* (+ 1 2) 3) 9))
(assert (eqv? (- (* 2 3) (/ 6 2)) 3))
""")

def test_fac():
    run_with_assert(r"""
(define (fac n)
  (if (eqv? n 0)
      1
      (* n (fac (- n 1)))
  )
)
(assert (eqv? (fac 1) 1))
(assert (eqv? (fac 5) 120))
(define (fac n)
  (define (fac-acc n acc)
    (if (eqv? n 0)
        acc
        (fac-acc (- n 1) (* n acc))
    )
  )
  (fac-acc n 1)
)
(assert (eqv? (fac 1) 1))
(assert (eqv? (fac 5) 120))
""")

def test_map():
    run_with_assert(r"""
(assert (equal?
  (map + '(1 2 3) '(4 5 6))
  '(5 7 9)
))
(assert (equal?
  (map (lambda (n) (+ n 1)) '(1 2 3 4))
  '(2 3 4 5)
))
(assert (equal?
  (map * '(1 2 3 4 5) '(1 2 3))
  '(1 4 9)
))
(assert (eq?
  (map (lambda (n) (assert #f "should not be reached")) '())
  '()
))
""")

def test_typepredicates():
    run_with_assert(r"""
(define some-objs
  (list #f #t 1 1.0 'symbol "string" #\c '(1 2) '() char? '#() '#(1 2)))   
(assert (equal?
  (map (lambda (test-func) (map test-func some-objs))
    (list boolean? number? symbol? string? char? pair? null? procedure? vector?))
  ;; #f #t 1 1.0 'symbol "string" #\c '(1 2) '() char? '#() '#(1 2)
  '((#t #t #f #f #f      #f       #f  #f     #f  #f    #f   #f) ; boolean?
    (#f #f #t #t #f      #f       #f  #f     #f  #f    #f   #f) ; number?
    (#f #f #f #f #t      #f       #f  #f     #f  #f    #f   #f) ; symbol?
    (#f #f #f #f #f      #t       #f  #f     #f  #f    #f   #f) ; string?
    (#f #f #f #f #f      #f       #t  #f     #f  #f    #f   #f) ; char?
    (#f #f #f #f #f      #f       #f  #t     #f  #f    #f   #f) ; pair?
    (#f #f #f #f #f      #f       #f  #f     #t  #f    #f   #f) ; null?
    (#f #f #f #f #f      #f       #f  #f     #f  #t    #f   #f) ; procedure?
    (#f #f #f #f #f      #f       #f  #f     #f  #f    #t   #t)); vector?
))
""")

def test_string():
    run_with_assert(r"""
(define new-str (make-string 7 #\*))
(assert (string? new-str))
(assert (equal? new-str "*******"))
""")

def test_closures():
    run_with_assert(r"""
(define (make-counter start) (lambda () (set! start (+ 1 start)) start))
(assert (procedure? make-counter))
(define counter-a (make-counter 10))
(define counter-b (make-counter 10))
(assert (procedure? counter-a))
(assert (eqv? (counter-a) 11))
(assert (eqv? (counter-a) 12))
(assert (eqv? (counter-a) 13))
(assert (eqv? (counter-b) 11))
""")

