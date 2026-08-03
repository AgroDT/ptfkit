//! Shared process-lifetime NumPy ufunc construction.

use std::{ffi::c_void, os::raw::c_char};

use numpy::npyffi::{objects::PyUFuncGenericFunction, ufunc};
use pyo3::prelude::*;

/// Creates a ufunc from static function and dtype tables.
///
/// # Safety
///
/// The supplied tables, name, and documentation must remain valid for the
/// lifetime of the Python process. NumPy retains these pointers.
pub unsafe fn create_ufunc(
    py: Python<'_>,
    functions: *mut PyUFuncGenericFunction,
    types: *mut c_char,
    nin: i32,
    nout: i32,
    name: *const c_char,
    documentation: *const c_char,
) -> PyResult<Py<PyAny>> {
    // SAFETY: upheld by the caller; NumPy returns a new owned Python reference.
    let pointer = unsafe {
        ufunc::PY_UFUNC_API.PyUFunc_FromFuncAndData(
            py,
            functions,
            std::ptr::null_mut::<*mut c_void>(),
            types,
            1,
            nin,
            nout,
            -1,
            name,
            documentation,
            0,
        )
    };
    if pointer.is_null() {
        Err(pyo3::exceptions::PyRuntimeError::new_err(
            "NumPy failed to create ufunc",
        ))
    } else {
        // SAFETY: NumPy transferred a new owned reference to us.
        Ok(unsafe { Bound::from_owned_ptr(py, pointer) }.unbind())
    }
}
