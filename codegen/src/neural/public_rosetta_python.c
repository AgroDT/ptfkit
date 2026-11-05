static PyObject *ptfkit_python_rosetta_data(PyObject *module, PyObject *unused) {
    (void)module;
    (void)unused;
    return PyBytes_FromStringAndSize((const char *)ptfkit_detail_rosetta3_data,
                                     PTFKIT_ROSETTA3_BYTES);
}

static PyObject *ptfkit_python_rosetta(PyObject *module, PyObject *args) {
    PyObject *capsule, *values;
    unsigned level, mode;
    if (!PyArg_ParseTuple(args, "OIIO", &capsule, &level, &mode, &values))
        return NULL;
    ptfkit_model *model = (ptfkit_model *)PyCapsule_GetPointer(capsule, "ptfkit.Model");
    if (!model)
        return NULL;
    double x[64], out[14];
    size_t count;
    if (!ptfkit_python_inputs(values, x, &count))
        return NULL;
    ptfkit_model_status status = ptfkit_rosetta3_predict(model, level, mode, x, count, out);
    if (status != PTFKIT_MODEL_OK)
        return ptfkit_python_failure(module, status);
    PyObject *result = PyTuple_New(14);
    if (!result)
        return NULL;
    for (Py_ssize_t i = 0; i < 14; ++i) {
        PyObject *v = PyFloat_FromDouble(out[i]);
        if (!v) {
            Py_DECREF(result);
            return NULL;
        }
        PyTuple_SET_ITEM(result, i, v);
    }
    return result;
}
