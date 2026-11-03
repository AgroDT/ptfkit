use ptfkit::{
    models::ModelError,
    zhang_schaap2017::{Estimate, Rosetta3},
};
fn run() -> Result<(), ModelError> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.len() < 6 {
        std::process::exit(2);
    }
    let model = if args[0] == "--builtin" {
        Rosetta3::builtin()?
    } else {
        Rosetta3::load(&args[0])?
    };
    let level: usize = args[1].parse().unwrap();
    let estimate = match args[2].as_str() {
        "0" => Estimate::Arithmetic,
        "1" => Estimate::Log10,
        "2" => Estimate::Geometric,
        _ => return Err(ModelError::Input),
    };
    let x: Vec<f64> = args[3..].iter().map(|v| v.parse().unwrap()).collect();
    let result = model.predict(level, estimate, &x)?;
    if matches!(estimate, Estimate::Arithmetic) {
        let named = match level {
            2 => model.calc_ptf_zhang2017_mod2(x[0], x[1], x[2])?,
            3 => model.calc_ptf_zhang2017_mod3(x[0], x[1], x[2], x[3])?,
            4 => model.calc_ptf_zhang2017_mod4(x[0], x[1], x[2], x[3], x[4])?,
            _ => model.calc_ptf_zhang2017_mod5(x[0], x[1], x[2], x[3], x[4], x[5])?,
        };
        assert_eq!(named.mean(), result.mean());
        assert_eq!(named.stddev(), result.stddev());
    }
    for value in result.mean().into_iter().chain(result.stddev()) {
        println!("{value:.17e}");
    }
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(match error {
            ModelError::Io(_) => 11,
            ModelError::Integrity => 12,
            ModelError::Format => 13,
            ModelError::Input => 15,
        });
    }
}
