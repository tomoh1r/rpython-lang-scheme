from __future__ import absolute_import

import os

from scheme import (
    object as ssobject,
    syntax,
    procedure,
    macro,
)
from scheme.ssparser import parse
from scheme.execution import ExecutionContext


_sys_dict = {}
for mod in (ssobject, syntax, procedure, macro):
    for obj_name in dir(mod):
        obj = getattr(mod, obj_name)
        try:
            issubclass(obj, ssobject.W_Callable)
            name = obj._symbol_name
            _sys_dict[name] = obj(name)
        except (TypeError, AttributeError):
            pass


_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, 'r5rs_derived_expr.ss')) as fp:
    de_expr_lst = parse(fp.read())


_sys_ctx = ExecutionContext(globalscope=_sys_dict)


# for expr in de_expr_lst:
#     expr.eval(_sys_ctx)
