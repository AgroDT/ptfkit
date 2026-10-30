#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "engine.h"

static PyObject *predict(PyObject *self, PyObject *args) {
    (void)self;
    unsigned level, mode;
    PyObject *values;
    if (!PyArg_ParseTuple(args, "IIO", &level, &mode, &values))
        return NULL;
    PyObject *seq = PySequence_Fast(values, "inputs must be a sequence");
    if (!seq)
        return NULL;
    Py_ssize_t count = PySequence_Fast_GET_SIZE(seq);
    if (count < 3 || count > 6) {
        Py_DECREF(seq);
        PyErr_SetString(PyExc_ValueError, "expected 3 to 6 predictors");
        return NULL;
    }
    double x[6], out[14];
    for (Py_ssize_t i = 0; i < count; ++i) {
        x[i] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(seq, i));
        if (PyErr_Occurred()) {
            Py_DECREF(seq);
            return NULL;
        }
    }
    Py_DECREF(seq);
    if (!ptfkit_calc_ptf_zhang2017(level, mode, x, (size_t)count, out)) {
        PyErr_SetString(PyExc_ValueError, "invalid level, estimate mode, or predictors");
        return NULL;
    }
    PyObject *result = PyTuple_New(14);
    if (!result)
        return NULL;
    for (Py_ssize_t i = 0; i < 14; ++i) {
        PyObject *item = PyFloat_FromDouble(out[i]);
        if (!item) {
            Py_DECREF(result);
            return NULL;
        }
        PyTuple_SET_ITEM(result, i, item);
    }
    return result;
}

static PyMethodDef methods[] = {
    {"calc_ptf_zhang2017", predict, METH_VARARGS,
     "Predict seven means followed by seven sample standard deviations.\n"
     "Arguments: level (2..5), mode (0 arithmetic, 1 log10, 2 geometric), predictors.\n"
     "Parameter order: theta_r, theta_s, alpha, n, Ksat, K0, L.\n"
     "Fixed-level validation rejects missing or invalid predictors."},
    {NULL, NULL, 0, NULL}};
static struct PyModuleDef module = {PyModuleDef_HEAD_INIT,
                                    "_rosetta3_local",
                                    "Local native Rosetta3 verification.",
                                    -1,
                                    methods,
                                    NULL,
                                    NULL,
                                    NULL,
                                    NULL};
PyMODINIT_FUNC PyInit__rosetta3_local(void) { return PyModule_Create(&module); }
