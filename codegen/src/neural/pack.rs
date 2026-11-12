//! Versioned, portable external dense-ensemble container. No executable content.
use super::Model;
pub(crate) fn encode(model: &Model) -> Vec<u8> {
    let mut out = b"PTFKNN01".to_vec();
    fn u32le(out: &mut Vec<u8>, value: usize) {
        out.extend_from_slice(&(value as u32).to_le_bytes());
    }
    u32le(&mut out, model.networks.len());
    for net in &model.networks {
        u32le(&mut out, net.nboot);
        u32le(&mut out, net.activations.len());
        for width in &net.widths {
            u32le(&mut out, *width);
        }
        for activation in &net.activations {
            u32le(
                &mut out,
                match activation.as_str() {
                    "linear" => 0,
                    "sigmoid" => 1,
                    "tansig" => 2,
                    "relu" => 3,
                    _ => unreachable!(),
                },
            );
        }
        for scale in net.inputs.iter().chain(&net.outputs) {
            u32le(
                &mut out,
                match scale.kind.as_str() {
                    "asis" => 0,
                    "division" => 1,
                    "logtr" => 2,
                    "affine" => 3,
                    "minmax" => 4,
                    "linear" => 5,
                    _ => unreachable!(),
                },
            );
            for i in 0..3 {
                out.extend_from_slice(&scale.params.get(i).copied().unwrap_or(0.0).to_le_bytes());
            }
        }
        out.extend_from_slice(&(net.offset as u64).to_le_bytes());
    }
    out.extend_from_slice(&(model.data.len() as u64).to_le_bytes());
    for value in &model.data {
        out.extend_from_slice(&value.to_le_bytes());
    }
    out
}
