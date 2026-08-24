#ifndef PTFKIT_USDA_TEXTURE_PARSER_H
#define PTFKIT_USDA_TEXTURE_PARSER_H

#include <stdint.h>

static int ptfkit_usda_texture_code(PyObject *value, uint8_t *code) {
    static const char *const names[] = {
        "sand", "loamy sand", "sandy loam", "loam", "silt loam", "silt",
        "sandy clay loam", "clay loam", "silty clay loam", "sandy clay",
        "silty clay", "clay",
    };
    if (!PyUnicode_CheckExact(value))
        return 0;
    for (uint8_t index = 0; index < 12; ++index) {
        int equal = PyUnicode_CompareWithASCIIString(value, names[index]);
        if (equal == 0) {
            *code = index;
            return 1;
        }
        if (equal == -1 && PyErr_Occurred())
            return -1;
    }
    return 0;
}

static PyObject *ptfkit_prepare_usda_texture(PyObject *self, PyObject *input) {
    (void)self;
    PyArrayObject *values = (PyArrayObject *)PyArray_FROM_OTF(input, NPY_OBJECT, NPY_ARRAY_ALIGNED);
    if (values == NULL)
        return NULL;
    PyArrayObject *codes = (PyArrayObject *)PyArray_SimpleNew(
        PyArray_NDIM(values), PyArray_DIMS(values), NPY_UINT8);
    if (codes == NULL) {
        Py_DECREF(values);
        return NULL;
    }
    PyObject *value_iterator = PyArray_IterNew((PyObject *)values);
    PyObject *code_iterator = PyArray_IterNew((PyObject *)codes);
    if (value_iterator == NULL || code_iterator == NULL) {
        Py_XDECREF(value_iterator);
        Py_XDECREF(code_iterator);
        Py_DECREF(values);
        Py_DECREF(codes);
        return NULL;
    }
    PyArrayIterObject *values_iter = (PyArrayIterObject *)value_iterator;
    PyArrayIterObject *codes_iter = (PyArrayIterObject *)code_iterator;
    npy_intp flat_index = 0;
    while (values_iter->index < values_iter->size) {
        PyObject *value = *(PyObject **)PyArray_ITER_DATA(values_iter);
        uint8_t code = 0;
        int valid = ptfkit_usda_texture_code(value, &code);
        if (valid <= 0) {
            if (valid == 0) {
                PyObject *representation = PyObject_Repr(value);
                if (representation != NULL) {
                    const char *text = PyUnicode_AsUTF8(representation);
                    if (text != NULL) {
                        if (PyArray_NDIM(values) == 0)
                            PyErr_Format(PyExc_ValueError, "invalid USDA texture class %s", text);
                        else
                            PyErr_Format(PyExc_ValueError, "invalid USDA texture class %s at flat index %zd", text, (Py_ssize_t)flat_index);
                    }
                    Py_DECREF(representation);
                }
            }
            Py_DECREF(value_iterator);
            Py_DECREF(code_iterator);
            Py_DECREF(values);
            Py_DECREF(codes);
            return NULL;
        }
        *(uint8_t *)PyArray_ITER_DATA(codes_iter) = code;
        PyArray_ITER_NEXT(values_iter);
        PyArray_ITER_NEXT(codes_iter);
        ++flat_index;
    }
    Py_DECREF(value_iterator);
    Py_DECREF(code_iterator);
    Py_DECREF(values);
    PyArray_CLEARFLAGS(codes, NPY_ARRAY_WRITEABLE);
    return (PyObject *)codes;
}

#endif
