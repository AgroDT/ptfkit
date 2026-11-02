static void ptfkit_python_qrf_free(PyObject *capsule) {
    ptfkit_euptf2_ths_free((ptfkit_euptf2_ths *)PyCapsule_GetPointer(capsule, "ptfkit.Euptf2Ths"));
}
static PyObject *ptfkit_python_qrf_load(PyObject *module, PyObject *args) {
    Py_buffer buffer;
    if (!PyArg_ParseTuple(args, "y*", &buffer)) return NULL;
    ptfkit_euptf2_ths *model = NULL;
    ptfkit_model_status status = ptfkit_euptf2_ths_from_bytes(
        (const unsigned char *)buffer.buf, (size_t)buffer.len, &model);
    PyBuffer_Release(&buffer);
    if (status != PTFKIT_MODEL_OK) return ptfkit_python_failure(module, status);
    PyObject *capsule = PyCapsule_New(model, "ptfkit.Euptf2Ths", ptfkit_python_qrf_free);
    if (!capsule) ptfkit_euptf2_ths_free(model);
    return capsule;
}
static PyObject *ptfkit_python_qrf_predict(PyObject *module, PyObject *args) {
    PyObject *capsule, *values;
    if (!PyArg_ParseTuple(args, "OO", &capsule, &values)) return NULL;
    ptfkit_euptf2_ths *model = (ptfkit_euptf2_ths *)PyCapsule_GetPointer(capsule, "ptfkit.Euptf2Ths");
    if (!model) return NULL;
    double x[64], out[4]; size_t count;
    if (!ptfkit_python_inputs(values, x, &count)) return NULL;
    ptfkit_model_status status = count == 4 ? ptfkit_euptf2_ths_predict(model, x, out) : PTFKIT_MODEL_INPUT;
    if (status != PTFKIT_MODEL_OK) return ptfkit_python_failure(module, status);
    return Py_BuildValue("(dddd)", out[0], out[1], out[2], out[3]);
}
