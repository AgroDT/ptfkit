//! Bundled dense networks compiled from YAML and shared semantic operations.
mod computation;
#[cfg(test)]
mod computation_tests;
#[allow(dead_code)] // Executed by emitted targets; the generator only needs its metadata types.
pub(crate) mod engine;
pub(crate) mod pack;
pub(crate) mod parameters;
pub(crate) mod public;
#[cfg(test)]
mod tests;
mod verification;
use thiserror::Error;
#[derive(Debug, Error)]
pub(crate) enum ModelError {
    #[error("inconsistent neural parameter declaration for network {network}")]
    ParameterDefinition { network: usize },
    #[error("unsupported dense model contract in {function}")]
    Contract { function: String },
    #[error("neural artifact SHA-256 mismatch")]
    Integrity,
    #[error("neural parameter data is non-finite, truncated, or has trailing values")]
    Data,
}

pub(crate) struct Model {
    pub(crate) networks: Vec<engine::Network>,
    pub(crate) data: Vec<f64>,
}
