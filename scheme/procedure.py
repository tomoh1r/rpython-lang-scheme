from __future__ import absolute_import

import py

from scheme.object import (
    W_Boolean, W_Pair, W_Symbol,
    W_Number, W_Real, W_Integer, W_List, W_Character, W_Vector,
    W_Procedure, W_String, W_Promise, plst2lst, w_undefined,
    SchemeQuit, WrongArgType, WrongArgsNumber,
    w_nil, w_true, w_false, lst2plst
)

##
# operations
##
class ListOper(W_Procedure):
    def procedure(self, ctx, lst):
        if len(lst) == 0:
            if self.default_result is None:
                raise WrongArgsNumber(len(lst), ">=1")

            return self.default_result

        if len(lst) == 1:
            if not isinstance(lst[0], W_Number):
                raise WrongArgType(lst[0], "Number")
            return self.unary_oper(lst[0])

        acc = None
        for arg in lst:
            if not isinstance(arg, W_Number):
                raise WrongArgType(arg, "Number")
            if acc is None:
                acc = arg
            else:
                acc = self.oper(acc, arg)

        return acc

    def unary_oper(self, x):
        if isinstance(x, W_Integer):
            return W_Integer(self.do_unary_oper(x.to_fixnum()))
        elif isinstance(x, W_Number):
            return W_Real(self.do_unary_oper(x.to_float()))
        else:
            raise WrongArgType(x, "Number")

    def oper(self, x, y):
        if isinstance(x, W_Integer) and isinstance(y, W_Integer):
            return W_Integer(self.do_oper(x.to_fixnum(), y.to_fixnum()))
        elif isinstance(x, W_Number) or isinstance(y, W_Number):
            return W_Real(self.do_oper(x.to_float(), y.to_float()))
        else:
            raise WrongArgType(x, "Number")

    def do_oper(self, x, y):
        raise NotImplementedError

    def do_unary_oper(self, x):
        raise NotImplementedError

def create_op_class(oper, unary_oper, title, default_result=None):
    class Op(ListOper):
        pass

    local_locals = {}
    attr_name = "do_oper"

    code = py.code.Source("""
    def %s(self, x, y):
        return x %s y
        """ % (attr_name, oper))

    exec code.compile() in local_locals
    local_locals[attr_name]._annspecialcase_ = 'specialize:argtype(1)'
    setattr(Op, attr_name, local_locals[attr_name])

    attr_name = "do_unary_oper"
    code = py.code.Source("""
    def %s(self, x):
        return %s x
        """ % (attr_name, unary_oper))

    exec code.compile() in local_locals
    local_locals[attr_name]._annspecialcase_ = 'specialize:argtype(1)'
    setattr(Op, attr_name, local_locals[attr_name])

    if default_result is None:
        Op.default_result = None
    else:
        Op.default_result = W_Integer(default_result)

    Op.__name__ = "Op" + title
    Op._symbol_name = oper
    return Op

Add = create_op_class('+', '', "Add", 0)
Sub = create_op_class('-', '-', "Sub")
Mul = create_op_class('*', '', "Mul", 1)
Div = create_op_class('/', '1 /', "Div")

class NumberComparison(W_Procedure):
    def procedure(self, ctx, lst):
        if len(lst) < 2:
            return W_Boolean(True)

        prev = lst[0]
        if not isinstance(prev, W_Number):
            raise WrongArgType(prev, "Number")

        for arg in lst[1:]:
            if not isinstance(arg, W_Number):
                raise WrongArgType(arg, "Number")

            if not self.relation(prev.to_number(), arg.to_number()):
                return W_Boolean(False)
            prev = arg

        return W_Boolean(True)

class Equal(NumberComparison):
    _symbol_name = "="

    def relation(self, a, b):
        return a == b

class LessThen(NumberComparison):
    _symbol_name = "<"

    def relation(self, a, b):
        return a < b

class LessEqual(NumberComparison):
    _symbol_name = "<="

    def relation(self, a, b):
        return a <= b

class GreaterThen(NumberComparison):
    _symbol_name = ">"

    def relation(self, a, b):
        return a > b

class GreaterEqual(NumberComparison):
    _symbol_name = ">="

    def relation(self, a, b):
        return a >= b


class List(W_Procedure):
    _symbol_name = "list"

    def procedure(self, ctx, lst):
        return plst2lst(lst)

class Cons(W_Procedure):
    _symbol_name = "cons"

    def procedure(self, ctx, lst):
        if len(lst) != 2:
            raise WrongArgsNumber(len(lst), 2)
        
        w_car = lst[0]
        w_cdr = lst[1]
        #cons is always creating a new pair
        return W_Pair(w_car, w_cdr)

class Car(W_Procedure):
    _symbol_name = "car"

    def procedure(self, ctx, lst):
        w_pair = lst[0]
        if not isinstance(w_pair, W_Pair):
            raise WrongArgType(w_pair, "Pair")
        return w_pair.car

class Cdr(W_Procedure):
    _symbol_name = "cdr"

    def procedure(self, ctx, lst):
        w_pair = lst[0]
        if not isinstance(w_pair, W_Pair):
            raise WrongArgType(w_pair, "Pair")
        return w_pair.cdr

class CarCdrCombination(W_Procedure):
    def procedure(self, ctx, lst):
        if len(lst) != 1:
            raise WrongArgsNumber(len(lst), 1)
        w_pair = lst[0]
        return self.do_oper(w_pair)

    def do_oper(self, w_pair):
        raise NotImplementedError

def gen_cxxxr_class(proc_name, oper_lst):
    class Cxxxr(CarCdrCombination):
        pass

    src_block = """
            w_iter = w_pair
            """
    oper_lst.reverse()
    for oper in oper_lst:
        src_block += """
            if not isinstance(w_iter, W_Pair):
                raise WrongArgType(w_iter, "Pair")
                """
        if oper == "car":
            src_block += """
            w_iter = w_iter.car
            """
        elif oper == "cdr":
            src_block += """
            w_iter = w_iter.cdr
            """
        else:
            raise ValueError("oper must 'car' or 'cdr'")

    src_block += """
            return w_iter
            """

    local_locals = {}
    attr_name = "do_oper"

    code = py.code.Source(("""
        def %s(self, w_pair):
            from scheme.object import W_Pair, WrongArgType
            """ % attr_name) + src_block)

    exec code.compile() in local_locals
    local_locals[attr_name]._annspecialcase_ = 'specialize:argtype(1)'
    setattr(Cxxxr, attr_name, local_locals[attr_name])

    Cxxxr._symbol_name = proc_name
    Cxxxr.__name__ = proc_name.capitalize()
    return Cxxxr

Caar = gen_cxxxr_class("caar", ['car', 'car'])
Cadr = gen_cxxxr_class("cadr", ['car', 'cdr'])
Cdar = gen_cxxxr_class("cdar", ['cdr', 'car'])
Cddr = gen_cxxxr_class("cddr", ['cdr', 'cdr'])
Caaar = gen_cxxxr_class("caaar", ['car', 'car', 'car'])
Caadr = gen_cxxxr_class("caadr", ['car', 'car', 'cdr'])
Cadar = gen_cxxxr_class("cadar", ['car', 'cdr', 'car'])
Caddr = gen_cxxxr_class("caddr", ['car', 'cdr', 'cdr'])
Cdaar = gen_cxxxr_class("cdaar", ['cdr', 'car', 'car'])
Cdadr = gen_cxxxr_class("cdadr", ['cdr', 'car', 'cdr'])
Cddar = gen_cxxxr_class("cddar", ['cdr', 'cdr', 'car'])
Cdddr = gen_cxxxr_class("cdddr", ['cdr', 'cdr', 'cdr'])
Caaaar = gen_cxxxr_class("caaaar", ['car', 'car', 'car', 'car'])
Caaadr = gen_cxxxr_class("caaadr", ['car', 'car', 'car', 'cdr'])
Caadar = gen_cxxxr_class("caadar", ['car', 'car', 'cdr', 'car'])
Caaddr = gen_cxxxr_class("caaddr", ['car', 'car', 'cdr', 'cdr'])
Cadaar = gen_cxxxr_class("cadaar", ['car', 'cdr', 'car', 'car'])
Cadadr = gen_cxxxr_class("cadadr", ['car', 'cdr', 'car', 'cdr'])
Caddar = gen_cxxxr_class("caddar", ['car', 'cdr', 'cdr', 'car'])
Cadddr = gen_cxxxr_class("cadddr", ['car', 'cdr', 'cdr', 'cdr'])
Cdaaar = gen_cxxxr_class("cdaaar", ['cdr', 'car', 'car', 'car'])
Cdaadr = gen_cxxxr_class("cdaadr", ['cdr', 'car', 'car', 'cdr'])
Cdadar = gen_cxxxr_class("cdadar", ['cdr', 'car', 'cdr', 'car'])
Cdaddr = gen_cxxxr_class("cdaddr", ['cdr', 'car', 'cdr', 'cdr'])
Cddaar = gen_cxxxr_class("cddaar", ['cdr', 'cdr', 'car', 'car'])
Cddadr = gen_cxxxr_class("cddadr", ['cdr', 'cdr', 'car', 'cdr'])
Cdddar = gen_cxxxr_class("cdddar", ['cdr', 'cdr', 'cdr', 'car'])
Cddddr = gen_cxxxr_class("cddddr", ['cdr', 'cdr', 'cdr', 'cdr'])

class SetCar(W_Procedure):
    _symbol_name = "set-car!"

    def procedure(self, ctx, lst):
        w_pair = lst[0]
        w_obj = lst[1]
        if not isinstance(w_pair, W_Pair):
            raise WrongArgType(w_pair, "Pair")

        w_pair.car = w_obj
        return w_undefined

class SetCdr(W_Procedure):
    _symbol_name = "set-cdr!"

    def procedure(self, ctx, lst):
        w_pair = lst[0]
        w_obj = lst[1]
        if not isinstance(w_pair, W_Pair):
            raise WrongArgType(w_pair, "Pair")

        w_pair.cdr = w_obj
        return w_undefined

class Append(W_Procedure):
    _symbol_name = "append"

    def procedure(self, ctx, lst):
        w_lol = plst2lst(lst)
        w_lol = Reverse().procedure(ctx,[w_lol])
        
        w_result = w_nil
        while w_lol is not w_nil:
            assert isinstance(w_lol, W_Pair)
            w_list = w_lol.car
            w_lol = w_lol.cdr
            if w_list is w_nil:
                continue
            if not isinstance(w_list, W_Pair):
                raise WrongArgType(w_list, "List")
            w_head = W_Pair(w_list.car, w_undefined)
            w_tail = w_head
            w_list = w_list.cdr
            while w_list is not w_nil:
                if not isinstance (w_list, W_Pair):
                    raise WrongArgType(w_list, "List")
                assert isinstance(w_tail, W_Pair)
                w_tail.cdr = W_Pair(w_list.car, w_undefined)
                w_tail = w_tail.cdr
                w_list = w_list.cdr

            assert isinstance(w_tail, W_Pair)
            w_tail.cdr = w_result
            w_result = w_head

        return w_result

class AppendE(W_Procedure):
    _symbol_name = "append!"

    def procedure(self, ctx, lst):
        if len(lst) == 0:
            return w_nil

        w_head = w_nil
        w_prev_tail = w_nil
        for w_list in lst:
            if w_list is w_nil:
                continue
            if w_head is w_nil:
                w_head = w_list
            if w_prev_tail is not w_nil:
                assert isinstance(w_prev_tail, W_Pair)
                w_prev_tail.cdr = w_list
            if not isinstance(w_list, W_Pair):
                raise WrongArgType(w_list, "List")
            while w_list.cdr is not w_nil:
                w_list = w_list.cdr
                if not isinstance(w_list, W_Pair):
                    raise WrongArgType(w_list, "List")        
            w_prev_tail = w_list

        return w_head

class Apply(W_Procedure):
    _symbol_name = "apply"

    def procedure_tr(self, ctx, lst):
        if len(lst) != 2:
            raise WrongArgsNumber(len(lst), 2)
        
        (w_procedure, w_lst) = lst
        if not isinstance(w_procedure, W_Procedure):
            #print w_procedure.to_repr(), "is not a procedure"
            raise WrongArgType(w_procedure, "Procedure")

        if not isinstance(w_lst, W_List):
            #print w_lst.to_repr(), "is not a list"
            raise WrongArgType(w_lst, "List")

        return w_procedure.procedure_tr(ctx, lst2plst(w_lst))

class Quit(W_Procedure):
    _symbol_name = "quit"

    def procedure(self, ctx, lst):
        raise SchemeQuit

class Force(W_Procedure):
    _symbol_name = "force"

    def procedure(self, ctx, lst):
        if len(lst) != 1:
            raise WrongArgsNumber(len(lst), 1)

        w_promise = lst[0]
        if not isinstance(w_promise, W_Promise):
            raise WrongArgType(w_promise, "Promise")

        return w_promise.force(ctx)

class Reverse(W_Procedure):
    _symbol_name = "reverse"

    def procedure(self, ctx, lst):
        if len(lst) != 1:
            raise WrongArgsNumber(len(lst), 1)
        w_inlist = lst[0]
        w_outlist = w_nil
        while w_inlist is not w_nil:
            if not isinstance(w_inlist, W_Pair):
                raise WrongArgType(lst[0], "List")
            w_outlist = W_Pair(w_inlist.car, w_outlist)
            w_inlist = w_inlist.cdr

        return w_outlist

class Map(W_Procedure):
    _symbol_name = "map"

    def procedure_tr(self, ctx, lst):
        if len(lst) < 2:
            raise WrongArgsNumber(len(lst), ">=2")

        w_proc = lst[0]
        if not isinstance(w_proc, W_Procedure):
            raise WrongArgType(w_proc, "Procedure")
        
        args_pending = lst[1:]
        args_len = len(args_pending)
        args_current = [None] * args_len
        w_rev_result = w_nil
        finished = False
        while True:
            for i in range(args_len):
                w_item = args_pending[i]
                if w_item is w_nil:
                    finished = True
                    break
                elif not isinstance(w_item, W_Pair):
                    raise WrongArgType(lst[i+1], "List")
                args_current[i]= w_item.car
                args_pending[i]= w_item.cdr

            if finished:
                break

            (w_call_res, iter_ctx) = w_proc.procedure_tr(ctx, args_current)
            while iter_ctx is not None:
                (w_call_res, iter_ctx) = w_call_res.eval_tr(iter_ctx)

            w_rev_result = W_Pair(w_call_res, w_rev_result)

        # XXX need to find out how to do this tailrecusive
        return (Reverse().procedure(ctx,[w_rev_result]), None)

class ForEach(W_Procedure):
    _symbol_name = "for-each"

    def procedure_tr(self, ctx, lst):
        # simply relay to map and ignore output
        (res, ctx) = Map().procedure_tr(ctx, lst)
        return (w_undefined, ctx)

class MakeString(W_Procedure):
    _symbol_name = "make-string"

    def procedure(self, ctx, lst):
        if len(lst) < 1 or len(lst) > 2:
            raise WrongArgsNumber(len(lst), "1-2")

        w_number = lst[0]
        if not isinstance(w_number, W_Integer):
            raise WrongArgType(w_number, "Integer")
        
        if len(lst) == 2:
            w_char = lst[1]
        else:
            w_char = W_Character(' ')
        if not isinstance(w_char, W_Character):
            raise WrongArgType(w_char, "Character")

        return W_String(w_char.to_string() * w_number.to_fixnum())

##
# Association lists
## 
class AssocX(W_Procedure):
    def procedure(self, ctx, lst):
        if len(lst) != 2:
            raise WrongArgsNumber(len(lst), 2)

        (w_obj, w_alst) = lst

        w_iter = w_alst
        while w_iter is not w_nil:
            if not isinstance(w_iter, W_Pair):
                raise WrongArgType(w_alst, "AList")

            w_item = w_iter.car

            if not isinstance(w_item, W_Pair):
                raise WrongArgType(w_alst, "AList")

            if self.compare(w_obj, w_item.car):
                return w_item

            w_iter = w_iter.cdr

        return w_false

    def compare(self, w_obj1, w_obj2):
        raise NotImplementedError

class Assq(AssocX):
    _symbol_name = "assq"

    def compare(self, w_obj1, w_obj2):
        return w_obj1.eq(w_obj2)

class Assv(AssocX):
    _symbol_name = "assv"

    def compare(self, w_obj1, w_obj2):
        return w_obj1.eqv(w_obj2)

class Assoc(AssocX):
    _symbol_name = "assoc"

    def compare(self, w_obj1, w_obj2):
        return w_obj1.equal(w_obj2)


##
# Member function
##
class MemX(W_Procedure):
    def procedure(self, ctx, lst):
        if len(lst) != 2:
            raise WrongArgsNumber(len(lst), 2)

        (w_obj, w_lst) = lst

        w_iter = w_lst
        while w_iter is not w_nil:
            if not isinstance(w_iter, W_Pair):
                raise WrongArgType(w_lst, "List")

            if self.compare(w_obj, w_iter.car):
                return w_iter

            w_iter = w_iter.cdr

        return w_false

    def compare(self, w_obj1, w_obj2):
        raise NotImplementedError
        
class Memq(MemX):
    _symbol_name = "memq"

    def compare(self, w_obj1, w_obj2):
        return w_obj1.eq(w_obj2)

class Memv(MemX):
    _symbol_name = "memv"

    def compare(self, w_obj1, w_obj2):
        return w_obj1.eqv(w_obj2)

class Member(MemX):
    _symbol_name = "member"

    def compare(self, w_obj1, w_obj2):
        return w_obj1.equal(w_obj2)

##
# Equivalnece Predicates
##
class EquivalnecePredicate(W_Procedure):
    def procedure(self, ctx, lst):
        if len(lst) != 2:
            raise WrongArgsNumber(len(lst), 2)
        (a, b) = lst
        return W_Boolean(self.predicate(a, b))

    def predicate(self, a, b):
        raise NotImplementedError

class EqP(EquivalnecePredicate):
    _symbol_name = "eq?"

    def predicate(self, a, b):
        return a.eq(b)

class EqvP(EquivalnecePredicate):
    _symbol_name = "eqv?"

    def predicate(self, a, b):
        return a.eqv(b)

class EqualP(EquivalnecePredicate):
    _symbol_name = "equal?"

    def predicate(self, a, b):
        return a.equal(b)

##
# Number Predicates
##
class PredicateNumber(W_Procedure):
    def procedure(self, ctx, lst):
        if len(lst) != 1:
            raise WrongArgsNumber(len(lst), 1)

        w_obj = lst[0]
        if not isinstance(w_obj, W_Number):
            raise WrongArgType(w_obj, "Number")

        return W_Boolean(self.predicate(w_obj))

    def predicate(self, w_obj):
        raise NotImplementedError

class NumberP(W_Procedure):
    # number? & Friends are applicable to any schemetype
    # not just numbers
    _symbol_name = "number?"

    def procedure(self, ctx, lst):
        if len(lst) != 1:
            raise WrongArgsNumber(len(lst), 1)

        w_obj = lst[0]
        if not isinstance(w_obj, W_Number):
            return W_Boolean(False)

        return W_Boolean(self.predicate(w_obj))

    def predicate(self, w_obj):
        return True

class IntegerP(NumberP):
    _symbol_name = "integer?"

    def predicate(self, w_obj):
        if not w_obj.exact:
            return w_obj.is_integer()

        return True

class RealP(NumberP):
    _symbol_name = "real?"

    def predicate(self, w_obj):
        return isinstance(w_obj, W_Real)

class RationalP(RealP):
    _symbol_name = "rational?"

class ComplexP(NumberP):
    _symbol_name = "complex?"

class ExactP(PredicateNumber):
    _symbol_name = "exact?"

    def predicate(self, w_obj):
        return w_obj.exact

class InexactP(PredicateNumber):
    _symbol_name = "inexact?"

    def predicate(self, w_obj):
        return not w_obj.exact

class ZeroP(PredicateNumber):
    _symbol_name = "zero?"

    def predicate(self, w_obj):
        return w_obj.to_number() == 0.0

class OddP(PredicateNumber):
    _symbol_name = "odd?"

    def predicate(self, w_obj):
        if not w_obj.is_integer():
            raise WrongArgType(w_obj, "Integer")

        return w_obj.round() % 2 != 0

class EvenP(PredicateNumber):
    _symbol_name = "even?"

    def predicate(self, w_obj):
        if not w_obj.is_integer():
            raise WrongArgType(w_obj, "Integer")

        return w_obj.round() % 2 == 0

##
# Type Predicates
##
class TypePredicate(W_Procedure):
    def procedure(self, ctx, lst):
        if len(lst) != 1:
            raise WrongArgsNumber(len(lst), 1)

        return W_Boolean(self.predicate(lst[0]))

    def predicate(self, w_obj):
        raise NotImplementedError

class BooleanP(TypePredicate):
    _symbol_name = "boolean?"

    def predicate(self, w_obj):
        return isinstance(w_obj, W_Boolean)

class SymbolP(TypePredicate):
    _symbol_name = "symbol?"

    def predicate(self, w_obj):
        return isinstance(w_obj, W_Symbol)

class StringP(TypePredicate):
    _symbol_name = "string?"

    def predicate(self, w_obj):
        return isinstance(w_obj, W_String)

class PairP(TypePredicate):
    _symbol_name = "pair?"

    def predicate(self, w_obj):
        return isinstance(w_obj, W_Pair)

class ProcedureP(TypePredicate):
    _symbol_name = "procedure?"

    def predicate(self, w_obj):
        return isinstance(w_obj, W_Procedure)

class CharP(TypePredicate):
    _symbol_name = "char?"

    def predicate(self, w_obj):
        return isinstance(w_obj, W_Character)

class VectorP(TypePredicate):
    _symbol_name = "vector?"

    def predicate(self, w_obj):
        return isinstance(w_obj, W_Vector)

class NullP(TypePredicate):
    _symbol_name = "null?"

    def predicate(self, w_obj):
        return w_obj is w_nil

class Not(W_Procedure):
    _symbol_name = "not"

    def procedure(self, ctx, lst):
        if len(lst) != 1:
            raise WrongArgsNumber(len(lst), 1)

        w_bool = lst[0]
        if w_bool.to_boolean():
            return w_false
        else:
            return w_true


##
# Input/Output procedures
##
class Display(W_Procedure):
    _symbol_name = "display"

    def procedure(self, ctx, lst):
        if len(lst) == 1:
            obj = lst[0]
        elif len(lst) == 2:
            (obj, port) = lst
            raise NotImplementedError
        else:
            raise WrongArgsNumber(len(lst), "1-2")

        print obj.to_string(),
        return w_undefined

class Newline(W_Procedure):
    _symbol_name = "newline"

    def procedure(self, ctx, lst):
        if len(lst) != 0:
            raise WrongArgsNumber(len(lst), 0)

        print
        return w_undefined

class Write(W_Procedure):
    _symbol_name = "write"

    def procedure(self, ctx, lst):
        if len(lst) == 1:
            obj = lst[0]
        elif len(lst) == 2:
            (obj, port) = lst
            raise NotImplementedError
        else:
            raise WrongArgsNumber(len(lst), "1-2")

        print obj.to_repr(),
        return w_undefined
