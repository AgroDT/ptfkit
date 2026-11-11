//! Local verification binds a scientific specification to the generic graph interpreter.
use super::{engine::Network, pipeline::Program};
fn program() -> Program {
    serde_json::from_str(include_str!(
        "../../../specs/models/rosetta3/computation.json"
    ))
    .expect("validated embedded computation")
}
pub fn valid(level: usize, x: &[f64]) -> bool {
    program().valid(level, x)
}
pub fn predict(
    networks: &[Network],
    data: &[f64],
    level: usize,
    mode: usize,
    x: &[f64],
) -> Option<[f64; 14]> {
    program()
        .evaluate(networks, data, level, mode, x)?
        .try_into()
        .ok()
}
