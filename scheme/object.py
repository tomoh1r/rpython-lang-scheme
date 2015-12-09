import py

class SchemeException(Exception):
    pass

class UnboundVariable(SchemeException):
    def __str__(self):
        return "Unbound variable %s" % (self.args[0], )

class NotCallable(SchemeException):
    def __str__(self):
        return "%s is not a callable" % (self.args[0].to_string(), )

class WrongArgsNumber(SchemeException):
    def __str__(self):
        if len(self.args) == 2:
            return ("Wrong number of args. Got: %d, expected: %s" %
                (self.args[0], self.args[1]))
        else:
            return "Wrong number of args."

class WrongArgType(SchemeException):
    def __str__(self):
        return "Wrong argument type: %s is not %s" % \
                (self.args[0].to_string(), self.args[1])

class SchemeSyntaxError(SchemeException):
    def __str__(self):
        return "Syntax error"

class SchemeQuit(SchemeException):
    """raised on (quit) evaluation"""
    pass

class W_Root(object):
    __slots__ = []

    def to_string(self):
        return '<%r>' % (self,)

    def to_repr(self):
        return "#<unknown>"

    def to_boolean(self):
        return True

    def __repr__(self):
        return "<" + self.__class__.__name__ + " " + self.to_string() + ">"

    def eval_cf(self, ctx, caller, cont, elst=[], enum=0):
        return self.eval(ctx)

    def eval(self, ctx):
        w_expr = self
        while ctx is not None:
            (w_expr, ctx) = w_expr.eval_tr(ctx)

        assert isinstance(w_expr, W_Root)
        return w_expr

    def eval_tr(self, ctx):
        return (self, None)

    def eq(self, w_obj):
        return self is w_obj
    eqv = eq
    equal = eqv

class W_Undefined(W_Root):
    def to_repr(self):
        return "#<undefined>"

    to_string = to_repr

w_undefined = W_Undefined()

class W_Symbol(W_Root):
    #class dictionary for symbol storage
    obarray = {}

    def __init__(self, val):
        self.name = val

    def to_repr(self):
        return self.name

    to_string = to_repr

    def eval_tr(self, ctx):
        w_obj = ctx.get(self.name)
        return (w_obj, None)

def symbol(name):
    #use this to create new symbols, it stores all symbols
    #in W_Symbol.obarray dict
    #if already in obarray return it 
    name = name.lower()
    w_symb = W_Symbol.obarray.get(name, None)
    if w_symb is None:
        w_symb = W_Symbol(name)
        W_Symbol.obarray[name] = w_symb

    assert isinstance(w_symb, W_Symbol)
    return w_symb

w_ellipsis = symbol("...")

class W_Boolean(W_Root):
    def __new__(cls, val):
        if val:
            return w_true
        else:
            return w_false

    def __init__(self, val):
        pass
            
class W_True(W_Boolean):
    _w_true = None
    def __new__(cls, val):
        if cls._w_true is None:
            cls._w_true = W_Root.__new__(cls)
        return cls._w_true

    def __init__(self, val):
        assert val

    def to_repr(self):
        return "#t"
    to_string = to_repr

w_true = W_True(True)

class W_False(W_Boolean):
    _w_false = None
    def __new__(cls, val):
        if cls._w_false is None:
            cls._w_false = W_Root.__new__(cls)
        return cls._w_false

    def __init__(self, val):
        assert not val

    def to_repr(self):
        return "#f"
    to_string = to_repr

    def to_boolean(self):
        return False

w_false = W_False(False)

class W_String(W_Root):
    def __init__(self, val):
        self.strval = val

    def to_string(self):
        return self.strval

    def to_repr(self):
        str_lst = ["\""]
        for ch in self.strval:
            if ch in ["\"", "\\"]:
                str_lst.append("\\" + ch)
            else:
                str_lst.append(ch)

        str_lst.append("\"")
        return ''.join(str_lst)

    def __repr__(self):
        return "<W_String \"" + self.strval + "\">"

    def equal(self, w_obj):
        if not isinstance(w_obj, W_String):
            return False
        return self.strval == w_obj.strval

_charname_to_char = {
    'space': ' ',
    'newline': '\n',
}

_char_to_charname = dict((v, k) for k, v in _charname_to_char.items())

class W_Character(W_Root):
    def __init__(self, val):
        if len(val) != 1:
            val = _charname_to_char.get(val.lower(), None)
            if val is None:
                raise SchemeSyntaxError
        self.chrval = val

    def to_string(self):
        return self.chrval

    def to_repr(self):
        charname = _char_to_charname.get(self.chrval, None)
        if charname is None:
            return "#\\" + self.chrval
        else:
            return "#\\" + charname

    def __repr__(self):
        return "<W_Character #\\" + self.chrval + ">"

    def eqv(self, w_obj):
        if not isinstance(w_obj, W_Character):
            return False
        return self.chrval == w_obj.chrval
    equal = eqv

class W_Real(W_Root):
    def __init__(self, val):
        self.exact = False
        self.realval = val

    def to_string(self):
        return str(self.realval)

    def to_repr(self):
        # return repr(self.realval)
        return str(float(self.realval))

    def to_number(self):
        return self.to_float()

    def to_fixnum(self):
        return int(self.realval)

    def to_float(self):
        return self.realval

    def round(self):
        int_part = int(self.realval)
        if self.realval > 0:
            if self.realval >= (int_part + 0.5):
                return int_part + 1

            return int_part

        else:
            if self.realval <= (int_part - 0.5):
                return int_part - 1

            return int_part

    def is_integer(self):
        return self.realval == self.round()

    def eqv(self, w_obj):
        return isinstance(w_obj, W_Real) \
                and self.exact is w_obj.exact \
                and self.realval == w_obj.realval
    equal = eqv

W_Number = W_Real

class W_Integer(W_Real):
    def __init__(self, val):
        self.intval = val
        self.realval = val
        self.exact = True

    def to_string(self):
        return str(self.intval)

    def to_repr(self):
        #return repr(self.intval)
        return str(int(self.intval))

    def to_number(self):
        return self.to_fixnum()

    def to_fixnum(self):
        return self.intval

    def to_float(self):
        return float(self.intval)

class W_Eval(W_Root):
    # this class is for objects which do more than
    # evaluate to themselves
    def eval_cf(self, ctx, caller, cont, elst=[], enum=0):
        #eval with continuation frame!
        ctx.cont_stack.append(ContinuationFrame(caller, cont, elst, enum))
        result = self.eval(ctx)
        ctx.cont_stack.pop()
        return result

    def continue_tr(self, ctx, lst, elst, cnt=True):
        raise NotImplementedError

class W_List(W_Eval):
    pass

class W_Nil(W_List):
    _w_nil = None
    def __new__(cls):
        if cls._w_nil is None:
            cls._w_nil = W_Root.__new__(cls)
        return cls._w_nil
    
    def __repr__(self):
        return "<W_Nil ()>"

    def to_repr(self):
        return "()"

    to_string = to_repr

    def eval_cf(self, ctx, caller, cont, elst=[], enum=0):
        raise SchemeSyntaxError

    def eval_tr(self, ctx):
        raise SchemeSyntaxError

w_nil = W_Nil()

class W_Pair(W_List):
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def to_string(self):
        return "(" + self.to_lstring() + ")"

    def to_lstring(self):
        car = self.car.to_string()
        cdr = self.cdr
        if isinstance(cdr, W_Pair): #still proper list
            return car + " " + cdr.to_lstring()
        elif cdr is w_nil: #end of proper list
            return car
        else: #end proper list with dotted
            return car + " . " + cdr.to_string()

    def to_repr(self):
        return "(" + self.to_lrepr() + ")"

    def to_lrepr(self):
        car = self.car.to_repr()
        cdr = self.cdr
        if isinstance(cdr, W_Pair): #still proper list
            return car + " " + cdr.to_lrepr()
        elif cdr is w_nil: #end of proper list
            return car
        else: #end proper list with dotted
            return car + " . " + cdr.to_repr()

    def __repr__(self):
        return "<W_Pair " + self.to_repr() + ">"

    def continue_tr(self, ctx, lst, elst, cnt=True):
        oper = elst[0]
        if not isinstance(oper, W_Callable):
            raise NotCallable(oper)

        cdr = lst
        if isinstance(cdr, W_List):
            result = oper.call_tr(ctx, cdr)
        else:
            raise SchemeSyntaxError

        if result[1] is None:
            result = result[0]
        else:
            result = result[0].eval(result[1])

        if len(ctx.cont_stack) == 0:
            raise ContinuationReturn(result)

        cont = ctx.cont_stack.pop()
        return cont.run(ctx, result)

    def eval_tr(self, ctx):
        oper = self.car.eval_cf(ctx, self, self.cdr)
        if not isinstance(oper, W_Callable):
            raise NotCallable(oper)

        #a proper (oper args ...) call
        # self.cdr has to be a proper list
        cdr = self.cdr
        if isinstance(cdr, W_List):
            return oper.call_tr(ctx, cdr)
        else:
            raise SchemeSyntaxError

    def get_car_as_pair(self):
        res = self.car
        if not isinstance(res, W_Pair):
            raise SchemeSyntaxError
        return res

    def get_cdr_as_pair(self):
        res = self.cdr
        if not isinstance(res, W_Pair):
            raise SchemeSyntaxError
        return res

    def equal(self, w_obj):
        return isinstance(w_obj, W_Pair) and \
                self.car.equal(w_obj.car) and \
                self.cdr.equal(w_obj.cdr)

class W_Vector(W_Root):
    def __init__(self, vect):
        self.vect = vect

    def to_repr(self):
        #strs = map(lambda item: item.to_repr(), self.vect)
        strs = []
        for w_item in self.vect:
            strs.append(w_item.to_repr())
        return "#(" + " ".join(strs) + ")"

    def to_string(self):
        #strs = map(lambda item: item.to_string(), self.vect)
        strs = []
        for w_item in self.vect:
            strs.append(w_item.to_string())
        return "#(" + " ".join(strs) + ")"

    def __repr__(self):
        return "<W_Vector [" + " ".join(self.vect) + "]>"

    def eval_tr(self, ctx):
        # vectors can not be evaluated
        raise SchemeSyntaxError

    def get_len(self):
        return len(self.vect)

    def get_item(self, offset):
        if offset < 0 or offset >= len(self.vect):
            raise SchemeException
        return self.vect[offset]

class W_Callable(W_Eval):
    def call_tr(self, ctx, lst):
        #usually tail-recursive call is normal call
        # which returns tuple with no further ExecutionContext
        return (self.call(ctx, lst), None)

    def call(self, ctx, lst):
        raise NotImplementedError

class Body(W_Eval):
    def __init__(self, body):
        self.body = body

    def __repr__(self):
        return "<Body " + self.to_string() + ">"

    def to_string(self):
        return self.body.to_string()

    def eval_tr(self, ctx):
        return self.continue_tr(ctx, self.body, [], False)

    def continue_tr(self, ctx, body, elst, cnt=True):
        body_expression = body
        while isinstance(body_expression, W_Pair):
            if body_expression.cdr is w_nil:
                if cnt is False:
                    return (body_expression.car, ctx)

                if ctx is None:
                    result = body_expression.car
                else:
                    result = body_expression.car.eval(ctx)

                if len(ctx.cont_stack) == 0:
                    raise ContinuationReturn(result)

                cont = ctx.cont_stack.pop()
                return cont.run(ctx, result)

            else:
                body_expression.car.eval_cf(ctx, self, body_expression.cdr)

            body_expression = body_expression.cdr

        raise SchemeSyntaxError

class W_Procedure(W_Callable):
    def __init__(self, pname=""):
        self.pname = pname

    def to_repr(self):
        return "#<primitive-procedure %s>" % (self.pname,)

    to_string = to_repr

    def call_tr(self, ctx, lst):
        return self.continue_tr(ctx, lst, [], False)

    def continue_tr(self, ctx, lst, elst, cnt=True):
        #evaluate all arguments into list
        arg_lst = elst
        arg_num = 0
        arg = lst
        while isinstance(arg, W_Pair):
            #this is non tail-call, it should create continuation frame
            # continuation frame consist:
            #  - plst of arleady evaluated arguments
            #  - arg (W_Pair) = arg.cdr as a pointer to not evaluated
            #    arguments
            #  - actual context
            w_obj = arg.car.eval_cf(ctx, self, arg.cdr, arg_lst, arg_num)

            arg_num += 1
            arg_lst.append(w_obj)
            arg = arg.cdr

        if arg is not w_nil:
            raise SchemeSyntaxError

        procedure_result = self.procedure_tr(ctx, arg_lst)
        if cnt is False:
            return procedure_result

        #if procedure_result still has to be evaluated
        # this can happen in case if self isinstance of W_Lambda
        if procedure_result[1] is None:
            procedure_result = procedure_result[0]
        else:
            procedure_result = procedure_result[0].eval(procedure_result[1])

        if len(ctx.cont_stack) == 0:
            raise ContinuationReturn(procedure_result)

        cont = ctx.cont_stack.pop()
        return cont.run(ctx, procedure_result)

    def procedure(self, ctx, lst):
        raise NotImplementedError

    def procedure_tr(self, ctx, lst):
        #usually tail-recursive procedure is normal procedure
        # which returns tuple with no further ExecutionContext
        return (self.procedure(ctx, lst), None)

class W_Macro(W_Callable):
    def __init__(self, pname=""):
        self.pname = pname

    def to_string(self):
        return "#<primitive-macro %s>" % (self.pname,)

class W_Promise(W_Root):
    def __init__(self, expr, ctx):
        self.expr = expr
        self.result = None
        self.closure = ctx

    def to_string(self):
        return "#<promise: %s>" % self.expr.to_string()

    def force(self, ctx):
        if self.result is None:
            #XXX cont_stack copy to be cont. friendly
            self.result = self.expr.eval(self.closure.copy())

        return self.result

class Formal(object):
    def __init__(self, name, islist=False):
        self.name = name
        self.islist = islist

class W_Lambda(W_Procedure):
    def __init__(self, args, body, closure, pname="#f"):
        self.args = []
        arg = args
        while not arg is w_nil:
            if isinstance(arg, W_Symbol):
                self.args.append(Formal(arg.to_string(), True))
                break
            else:
                if not isinstance(arg, W_Pair):
                    raise SchemeSyntaxError
                if not isinstance(arg.car, W_Symbol):
                    raise WrongArgType(arg.car, "Identifier")
                #list of argument names, not evaluated
                self.args.append(Formal(arg.car.to_string(), False))
                arg = arg.cdr

        self.body = Body(body)
        self.pname = pname
        self.closure = closure

    def to_string(self):
        return "#<procedure %s>" % (self.pname,)

    def procedure_tr(self, ctx, lst):
        #must be tail-recursive aware, uses eval_body
        #ctx is a caller context, which is joyfully ignored

        local_ctx = self.closure.copy()
        #if lambda procedure should keep caller cont_stack
        local_ctx.cont_stack = ctx.cont_stack #[:]

        #set lambda arguments
        for idx in range(len(self.args)):
            formal = self.args[idx]
            if formal.islist:
                local_ctx.put(formal.name, plst2lst(lst[idx:]))
            else:
                local_ctx.put(formal.name, lst[idx])

        return self.body.eval_tr(local_ctx)


##
# General helpers
##
def plst2lst(plst, w_cdr=w_nil):
    """coverts python list() of W_Root into W_Pair scheme list"""
    plst.reverse()
    for w_obj in plst:
        w_cdr = W_Pair(w_obj, w_cdr)

    return w_cdr

def lst2plst(w_list):
    """coverts W_Pair scheme list into a python list() of W_Root"""
    lst = []
    w_iter = w_list
    while w_iter is not w_nil:
        if not isinstance(w_iter, W_Pair):
            raise WrongArgType(w_list, "List")
        lst.append(w_iter.car)
        w_iter = w_iter.cdr

    return lst

##
# Continuations
##
class ContinuationReturn(SchemeException):
    def __init__(self, result):
        self.result = result

class ContinuationFrame(object):
    def __init__(self, caller, continuation, evaluated_args = [], enum=0):
        self.caller = caller
        assert isinstance(continuation, W_Root)
        self.continuation = continuation
        assert isinstance(evaluated_args, list)
        self.evaluated_args = evaluated_args
        self.evaluated_args_num = enum

    def run(self, ctx, arg):
        elst = self.evaluated_args[:self.evaluated_args_num]
        elst.append(arg)
        #print 'c>', self.caller, elst, self.continuation
        return self.caller.continue_tr(ctx, self.continuation, elst, True)

class Continuation(W_Procedure):
    def __init__(self, ctx, continuation):
        self.closure = ctx
        #copy of continuation stack this means that cont_stack is not
        # global, so watch out with closures
        self.cont_stack = continuation[:]
        try:
            self.continuation = self.cont_stack.pop()
        except IndexError:
            #continuation captured on top-level
            self.continuation = None

    def __repr__(self):
        return self.to_string()

    def to_string(self):
        return "#<continuation -> %s>" % (self.continuation,)

    def procedure_tr(self, ctx, lst):
        #caller ctx is ignored
        if len(lst) == 0:
            lst.append(w_undefined)

        #print "Continuation called", self.cont_stack
        self.closure.cont_stack = self.cont_stack[:]
        cont = self.continuation
        if cont is None:
            raise ContinuationReturn(lst[0])

        return cont.run(self.closure, lst[0])

class CallCC(W_Procedure):
    _symbol_name = "call/cc"

    def procedure_tr(self, ctx, lst):
        if len(lst) != 1 or not isinstance(lst[0], W_Procedure):
            #print lst[0]
            raise SchemeSyntaxError

        w_lambda = lst[0]
        if not isinstance(w_lambda, W_Procedure):
            raise SchemeSyntaxError
        cc = Continuation(ctx, ctx.cont_stack)
        return w_lambda.call_tr(ctx, W_Pair(cc, w_nil))

