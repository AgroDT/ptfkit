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

static void ptfkit_python_euptf2_free(PyObject *capsule) {
    ptfkit_euptf2_free((ptfkit_euptf2_model*)PyCapsule_GetPointer(capsule,"ptfkit.Euptf2Model"));
}
static PyObject *ptfkit_python_euptf2_load(PyObject *module,PyObject *args) {
    const char *name; Py_buffer buffer;
    if(!PyArg_ParseTuple(args,"sy*",&name,&buffer)) return NULL;
    ptfkit_euptf2_model *model=NULL;
    ptfkit_model_status status=ptfkit_euptf2_from_bytes(name,(const unsigned char*)buffer.buf,(size_t)buffer.len,&model);
    PyBuffer_Release(&buffer);
    if(status!=PTFKIT_MODEL_OK) return ptfkit_python_failure(module,status);
    PyObject *capsule=PyCapsule_New(model,"ptfkit.Euptf2Model",ptfkit_python_euptf2_free);
    if(!capsule) ptfkit_euptf2_free(model);
    return capsule;
}
static PyObject *ptfkit_python_euptf2_predict(PyObject *module,PyObject *args) {
    PyObject *capsule,*inputs,*probabilities;
    if(!PyArg_ParseTuple(args,"OOO",&capsule,&inputs,&probabilities)) return NULL;
    ptfkit_euptf2_model *model=(ptfkit_euptf2_model*)PyCapsule_GetPointer(capsule,"ptfkit.Euptf2Model");
    if(!model) return NULL;
    double x[64],p[64],mean[7],quantiles[384]; size_t nin,nq;
    if(!ptfkit_python_inputs(inputs,x,&nin) || !ptfkit_python_inputs(probabilities,p,&nq)) return NULL;
    size_t nm=model->detail_contract->means,nc=model->detail_contract->components;
    ptfkit_model_status status=ptfkit_euptf2_predict(model,x,nin,p,nq,mean,nm,quantiles,nc*nq);
    if(status!=PTFKIT_MODEL_OK) return ptfkit_python_failure(module,status);
    PyObject *means=PyTuple_New((Py_ssize_t)nm),*rows=PyTuple_New((Py_ssize_t)nc);
    if(!means || !rows) { Py_XDECREF(means); Py_XDECREF(rows); return NULL; }
    for(size_t i=0;i<nm;++i) {
        PyObject *v=PyFloat_FromDouble(mean[i]);
        if(!v) { Py_DECREF(means); Py_DECREF(rows); return NULL; }
        PyTuple_SET_ITEM(means,(Py_ssize_t)i,v);
    }
    for(size_t i=0;i<nc;++i) {
        PyObject *row=PyTuple_New((Py_ssize_t)nq);
        if(!row) { Py_DECREF(means); Py_DECREF(rows); return NULL; }
        for(size_t j=0;j<nq;++j) {
            PyObject *v=PyFloat_FromDouble(quantiles[i*nq+j]);
            if(!v) { Py_DECREF(row); Py_DECREF(means); Py_DECREF(rows); return NULL; }
            PyTuple_SET_ITEM(row,(Py_ssize_t)j,v);
        }
        PyTuple_SET_ITEM(rows,(Py_ssize_t)i,row);
    }
    PyObject *result=PyTuple_Pack(2,means,rows);
    Py_DECREF(means); Py_DECREF(rows); return result;
}
