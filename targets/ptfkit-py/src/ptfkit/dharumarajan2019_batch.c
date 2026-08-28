#include <ptfkit/dharumarajan2019.h>
#include <ptfkit/dharumarajan2019_batch.h>

#include "ufunc.h"

static int calc_ptf_dharumarajan2019_infiltration_batch_contiguous_loop(
    PyArrayMethod_Context *context, char *const *data, const npy_intp *dimensions,
    const npy_intp *strides, NpyAuxData *transferdata) {
    (void)context;
    (void)strides;
    (void)transferdata;
    calc_ptf_dharumarajan2019_infiltration_batch(
        (const double *)data[0], (const double *)data[1], (const double *)data[2],
        (double *)data[3], (size_t)dimensions[0]);
    return 0;
}

static int calc_ptf_dharumarajan2019_infiltration_batch_strided_loop(
    PyArrayMethod_Context *context, char *const *data, const npy_intp *dimensions,
    const npy_intp *strides, NpyAuxData *transferdata) {
    (void)context;
    (void)transferdata;
    for (npy_intp index = 0; index < dimensions[0]; ++index) {
        *(double *)(data[3] + index * strides[3]) = calc_ptf_dharumarajan2019_infiltration(
            *(const double *)(data[0] + index * strides[0]),
            *(const double *)(data[1] + index * strides[1]),
            *(const double *)(data[2] + index * strides[2]));
    }
    return 0;
}

static PyType_Slot calc_ptf_dharumarajan2019_infiltration_batch_slots[] = {
    {NPY_METH_strided_loop, calc_ptf_dharumarajan2019_infiltration_batch_strided_loop},
    {NPY_METH_contiguous_loop, calc_ptf_dharumarajan2019_infiltration_batch_contiguous_loop},
    {0, NULL},
};

static PyArrayMethod_Spec calc_ptf_dharumarajan2019_infiltration_batch_spec = {
    .name = "calc_ptf_dharumarajan2019_infiltration_batch",
    .nin = 3,
    .nout = 1,
    .casting = NPY_SAME_KIND_CASTING,
    .slots = calc_ptf_dharumarajan2019_infiltration_batch_slots,
};

static int ptfkit_register_dharumarajan2019_batch(PyObject *module) {
    return ptfkit_add_ufunc(module, "calc_ptf_dharumarajan2019_infiltration_batch", 3, 1,
                            &calc_ptf_dharumarajan2019_infiltration_batch_spec);
}
