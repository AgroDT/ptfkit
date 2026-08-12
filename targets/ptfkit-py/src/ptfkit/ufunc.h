#pragma once

#include <math.h>

static inline int ptfkit_add_ufunc(
    PyObject *module,
    const char *name,
    PyUFuncGenericFunction *functions,
    char *types,
    int nin,
    int nout
) {
    PyObject *ufunc = PyUFunc_FromFuncAndData(
        functions, NULL, types, 1, nin, nout, PyUFunc_None, name, NULL, 0
    );
    if (ufunc == NULL) return -1;
    return PyModule_AddObject(module, name, ufunc);
}
