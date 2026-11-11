use super::*;
use serde_json::json;

fn fixture() -> (Program, Manifest) {
    let program = serde_json::from_value(json!({
        "format_version":1,"network_manifest":"network.json","levels":{"2":1},"estimates":3,"outputs":4,
        "input_conditions":[{"left":"x.0","op":"ge","right":0,"minimum_level":2}],
        "nodes":[
            {"id":"raw","op":"network","networks":{"2":0},"source":"x"},
            {"id":"physical","op":"pow10","source":"raw","columns":[0]},
            {"id":"log","op":"statistics","source":"raw","ddof":1},
            {"id":"linear","op":"statistics","source":"physical","ddof":1},
            {"id":"geo","op":"pow10","source":"log_mean","columns":[0]},
            {"id":"mean","op":"select","choices":["linear_mean","log_mean","geo"]},
            {"id":"std","op":"select","choices":["linear_std","log_std","linear_std"]},
            {"id":"primary","op":"store","indices":[0,1],"values":["mean.0","std.0"]},
            {"id":"feed","op":"select","choices":["linear_mean","geo","geo"]},
            {"id":"input","op":"gather","values":["feed.0"]},
            {"id":"domain","op":"guard","conditions":[{"left":"input.0","op":"gt","right":0,"minimum_level":2}]},
            {"id":"secondary","op":"network","networks":{"2":1},"source":"input"},
            {"id":"summary","op":"statistics","source":"secondary","ddof":1},
            {"id":"result","op":"store","indices":[2,3],"values":["summary_mean.0","summary_std.0"]}
        ]
    })).unwrap();
    let network = json!({"name":"controlled","nboot":2,"widths":[1,1],"activations":["linear"],
        "inputs":[{"kind":"asis","params":[]}],"outputs":[{"kind":"asis","params":[]}],"offset":0});
    let mut second = network.clone();
    second["offset"] = json!(4);
    let manifest = serde_json::from_value(
        json!({"format_version":1,"upstream_revision":"hand arithmetic",
        "artifact":"models.bin","sha256":"unused","networks":[network,second]}),
    )
    .unwrap();
    (program, manifest)
}

#[test]
fn renders_ordered_composition_from_a_controlled_graph() {
    let (program, manifest) = fixture();
    let output = render(&program, &manifest).unwrap();
    snapbox::assert_data_eq!(
        output.c,
        snapbox::file!("../fixtures/expected/neural_pipeline.c")
    );
    snapbox::assert_data_eq!(
        output.rust,
        snapbox::file!("../fixtures/expected/neural_pipeline.rs")
    );
}

#[test]
fn composition_distinguishes_member_transforms_and_aggregate_transforms() {
    let (program, _) = fixture();
    // Constant primary members [0,2]; secondary members [v,2v].
    // Mean(10^[0,2])=50.5, 10^mean([0,2])=10; sample SDs use n-1.
    let scale = || super::super::engine::Scale {
        kind: "asis".into(),
        params: vec![],
    };
    let network = |offset| super::super::engine::Network {
        nboot: 2,
        widths: vec![1, 1],
        activations: vec!["linear".into()],
        inputs: vec![scale()],
        outputs: vec![scale()],
        offset,
    };
    let networks = [network(0), network(4)];
    let data = [0.0, 0.0, 0.0, 2.0, 1.0, 0.0, 2.0, 0.0];
    for (mode, expected) in [
        (
            0,
            [50.5, 99.0 / 2.0_f64.sqrt(), 75.75, 50.5 / 2.0_f64.sqrt()],
        ),
        (1, [1.0, 2.0_f64.sqrt(), 15.0, 10.0 / 2.0_f64.sqrt()]),
        (
            2,
            [10.0, 99.0 / 2.0_f64.sqrt(), 15.0, 10.0 / 2.0_f64.sqrt()],
        ),
    ] {
        let actual = program.evaluate(&networks, &data, 2, mode, &[0.0]).unwrap();
        for (actual, expected) in actual.iter().zip(expected) {
            assert!((actual - expected).abs() < 1e-12);
        }
    }
    assert!(program.evaluate(&networks, &data, 2, 0, &[-1.0]).is_none());
}

#[test]
fn rejects_invalid_graph_edges_shapes_and_statistics() {
    for change in 0..7 {
        let (mut program, mut manifest) = fixture();
        match change {
            0 => {
                if let Operation::Pow10 { source, .. } = &mut program.nodes[1].operation {
                    *source = "future".into();
                }
            }
            1 => {
                if let Operation::Pow10 { columns, .. } = &mut program.nodes[1].operation {
                    *columns = vec![1];
                }
            }
            2 => {
                if let Operation::Statistics { ddof, .. } = &mut program.nodes[2].operation {
                    *ddof = 0;
                }
            }
            3 => manifest.networks[1].widths[0] = 2,
            4 => {
                if let Operation::Select { choices } = &mut program.nodes[5].operation {
                    choices.pop();
                }
            }
            5 => {
                if let Operation::Store { indices, .. } = &mut program.nodes[7].operation {
                    indices[1] = 0;
                }
            }
            _ => {
                if let Operation::Pow10 { columns, .. } = &mut program.nodes[1].operation {
                    *columns = vec![0, 0];
                }
            }
        }
        assert!(
            matches!(
                render(&program, &manifest),
                Err(ModelError::Pipeline { .. })
            ),
            "accepted malformed graph {change}"
        );
    }
}
