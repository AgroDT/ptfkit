#include <ptfkit/li2007.h>
#include <ptfkit/li2007_batch.h>

#include "ufunc.h"

static int calc_ptf_li2007_batch_contiguous_loop(PyArrayMethod_Context *context, char *const *data,
                                                 const npy_intp *dimensions,
                                                 const npy_intp *strides,
                                                 NpyAuxData *transferdata) {
    (void)context;
    (void)strides;
    (void)transferdata;
    calc_ptf_li2007_batch((const double *)data[0], (const double *)data[1], (const double *)data[2],
                          (const double *)data[3], (const double *)data[4], (double *)data[5],
                          (double *)data[6], (double *)data[7], (double *)data[8],
                          (size_t)dimensions[0]);
    return 0;
}

static int calc_ptf_li2007_batch_strided_loop(PyArrayMethod_Context *context, char *const *data,
                                              const npy_intp *dimensions, const npy_intp *strides,
                                              NpyAuxData *transferdata) {
    (void)context;
    (void)transferdata;
    for (npy_intp index = 0; index < dimensions[0]; ++index) {
        const li2007_ptf_result result =
            calc_ptf_li2007(*(const double *)(data[0] + index * strides[0]),
                            *(const double *)(data[1] + index * strides[1]),
                            *(const double *)(data[2] + index * strides[2]),
                            *(const double *)(data[3] + index * strides[3]),
                            *(const double *)(data[4] + index * strides[4]));
        *(double *)(data[5] + index * strides[5]) = result.theta_s;
        *(double *)(data[6] + index * strides[6]) = result.a_vg;
        *(double *)(data[7] + index * strides[7]) = result.n_vg;
        *(double *)(data[8] + index * strides[8]) = result.k_sat;
    }
    return 0;
}

static PyType_Slot calc_ptf_li2007_batch_slots[] = {
    {NPY_METH_strided_loop, calc_ptf_li2007_batch_strided_loop},
    {NPY_METH_contiguous_loop, calc_ptf_li2007_batch_contiguous_loop},
    {0, NULL},
};

static PyArrayMethod_Spec calc_ptf_li2007_batch_spec = {
    .name = "calc_ptf_li2007_batch",
    .nin = 5,
    .nout = 4,
    .casting = NPY_SAME_KIND_CASTING,
    .slots = calc_ptf_li2007_batch_slots,
};

static int ptfkit_register_li2007_batch(PyObject *module) {
    return ptfkit_add_ufunc(module, "calc_ptf_li2007_batch", 5, 4, &calc_ptf_li2007_batch_spec);
}
