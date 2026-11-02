use ptfkit::models::{Euptf2Model, Euptf2Ths, ModelError};
use std::io::BufRead;

fn run() -> Result<(), ModelError> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.first().is_some_and(|s| s == "--collection") {
        if args.len() < 3 {
            return Err(ModelError::Input);
        }
        let model = Euptf2Model::load(&args[1], &args[2])?;
        let probabilities: Vec<f64> = args[3..]
            .iter()
            .map(|s| s.parse().map_err(|_| ModelError::Input))
            .collect::<Result<_, _>>()?;
        for line in std::io::stdin().lock().lines() {
            let line = line.map_err(ModelError::Io)?;
            let inputs: Result<Vec<f64>, _> = line.split_whitespace().map(str::parse).collect();
            let result = inputs.map_err(|_| ModelError::Input).and_then(|x| {
                if probabilities.is_empty() {
                    model.predict(&x)
                } else {
                    model.predict_quantiles(&x, &probabilities)
                }
            });
            match result {
                Ok(p) => {
                    for v in p.mean.into_iter().chain(p.quantiles.into_iter().flatten()) {
                        print!("{v:.17e} ");
                    }
                    println!();
                }
                Err(ModelError::Input) => println!("error15"),
                Err(e) => return Err(e),
            }
        }
        return Ok(());
    }
    if args.len() != 5 {
        return Err(ModelError::Input);
    }
    let model = Euptf2Ths::load(&args[0])?;
    let mut inputs = [0.0; 4];
    for (out, value) in inputs.iter_mut().zip(&args[1..]) {
        *out = value.parse().map_err(|_| ModelError::Input)?;
    }
    for value in model.predict(inputs)? {
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
