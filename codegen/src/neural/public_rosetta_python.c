static PyObject *ptfkit_python_rosetta_builtin(PyObject *module, PyObject *unused) {
    (void)unused;
    ptfkit_model *model=NULL;
    ptfkit_model_status status=ptfkit_rosetta3_builtin(&model);
    if(status!=PTFKIT_MODEL_OK)return ptfkit_python_failure(module,status);
    PyObject *capsule=PyCapsule_New(model,"ptfkit.Model",ptfkit_python_model_free);
    if(!capsule)ptfkit_model_free(model);
    return capsule;
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
    ptfkit_model_status status;
    PyThreadState *thread_state = PyEval_SaveThread();
    status = ptfkit_rosetta3_predict(model, level, mode, x, count, out);
    PyEval_RestoreThread(thread_state);
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

/* Python normalizes dtypes and broadcasting; this bridge owns strided iteration. */
static PyObject *ptfkit_python_rosetta_batch(PyObject *module, PyObject *args) {
    PyObject *capsule, *inputs, *outputs;
    unsigned level, mode;
    if (!PyArg_ParseTuple(args, "OIIOO", &capsule, &level, &mode, &inputs, &outputs))
        return NULL;
    ptfkit_model *model = (ptfkit_model *)PyCapsule_GetPointer(capsule, "ptfkit.Model");
    if (!model)
        return NULL;
    PyObject *in = PySequence_Fast(inputs, "inputs must be a sequence");
    if (!in)
        return NULL;
    PyObject *out = PySequence_Fast(outputs, "outputs must be a sequence");
    if (!out) {
        Py_DECREF(in);
        return NULL;
    }
    Py_buffer buffers[20] = {{0}};
    Py_ssize_t acquired = 0, count = (Py_ssize_t)level + 1, total = 1;
    ptfkit_model_status status = PTFKIT_MODEL_INPUT;
    if (level < 2 || level > 5 || mode > 2 || PySequence_Fast_GET_SIZE(in) != count ||
        PySequence_Fast_GET_SIZE(out) != 14)
        goto cleanup;
    for (Py_ssize_t i = 0; i < count + 14; ++i) {
        PyObject *array =
            i < count ? PySequence_Fast_GET_ITEM(in, i) : PySequence_Fast_GET_ITEM(out, i - count);
        if (PyObject_GetBuffer(array, &buffers[i],
                               PyBUF_STRIDES | PyBUF_FORMAT | (i < count ? 0 : PyBUF_WRITABLE)) < 0)
            goto cleanup;
        ++acquired;
        if (buffers[i].itemsize != sizeof(double) || !buffers[i].format ||
            strcmp(buffers[i].format, "d") || buffers[i].suboffsets ||
            buffers[i].ndim != buffers[0].ndim)
            goto cleanup;
        for (int d = 0; d < buffers[0].ndim; ++d)
            if (buffers[i].shape[d] != buffers[0].shape[d])
                goto cleanup;
    }
    for (int d = 0; d < buffers[0].ndim; ++d) {
        Py_ssize_t size = buffers[0].shape[d];
        if (size && total > PY_SSIZE_T_MAX / size)
            goto cleanup;
        total *= size;
    }
    status = PTFKIT_MODEL_OK;
    PyThreadState *thread_state = PyEval_SaveThread();
    for (Py_ssize_t sample = 0; sample < total; ++sample) {
        double x[6], values[14];
        char *addresses[20];
        for (Py_ssize_t i = 0; i < acquired; ++i) {
            addresses[i] = (char *)buffers[i].buf;
            Py_ssize_t remainder = sample;
            for (int d = buffers[i].ndim - 1; d >= 0; --d) {
                addresses[i] += (remainder % buffers[i].shape[d]) * buffers[i].strides[d];
                remainder /= buffers[i].shape[d];
            }
            if (i < count)
                memcpy(&x[i], addresses[i], sizeof(double));
        }
        status = ptfkit_rosetta3_predict(model, level, mode, x, (size_t)count, values);
        if (status != PTFKIT_MODEL_OK)
            break;
        for (Py_ssize_t i = 0; i < 14; ++i)
            memcpy(addresses[count + i], &values[i], sizeof(double));
    }
    PyEval_RestoreThread(thread_state);
cleanup:
    for (Py_ssize_t i = 0; i < acquired; ++i)
        PyBuffer_Release(&buffers[i]);
    Py_DECREF(in);
    Py_DECREF(out);
    if (PyErr_Occurred())
        return NULL;
    if (status != PTFKIT_MODEL_OK)
        return ptfkit_python_failure(module, status);
    Py_RETURN_NONE;
}
