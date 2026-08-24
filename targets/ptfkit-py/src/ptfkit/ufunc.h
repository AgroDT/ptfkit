#pragma once

#include <math.h>

static inline double ptfkit_pow4(double value) {
    const double square = value * value;
    return square * square;
}

static inline int ptfkit_add_ufunc(PyObject *module, const char *name, const int *types, int nin,
                                   int nout, PyArrayMethod_Spec *spec) {
    PyArray_DTypeMeta *dtypes[NPY_MAXARGS];
    for (int argument = 0; argument < nin + nout; argument++) {
        dtypes[argument] =
            types[argument] == NPY_UINT32 ? &PyArray_UInt32DType : &PyArray_DoubleDType;
    }
    spec->dtypes = dtypes;
    PyObject *ufunc =
        PyUFunc_FromFuncAndData(NULL, NULL, NULL, 0, nin, nout, PyUFunc_None, name, NULL, 0);
    if (ufunc == NULL)
        return -1;
    if (PyUFunc_AddLoopFromSpec(ufunc, spec) < 0) {
        Py_DECREF(ufunc);
        return -1;
    }
    return PyModule_AddObject(module, name, ufunc);
}
