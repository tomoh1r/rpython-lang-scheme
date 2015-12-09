
import scheme.object as ssobject
import scheme.syntax as syntax
import scheme.procedure as procedure
import scheme.macro as macro
from scheme.ssparser import parse


from scheme.execution import ExecutionContext, Location

import py

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

de_file = py.path.local(__file__).dirpath().join("r5rs_derived_expr.ss")
de_code = de_file.read()
de_expr_lst = parse(de_code)

_sys_ctx = ExecutionContext(globalscope = _sys_dict)

#for expr in de_expr_lst:
#    expr.eval(_sys_ctx)
