use ptfkit::models::{Euptf2Ths, ModelError};

fn run() -> Result<(), ModelError> {
    let args: Vec<String> = std::env::args().skip(1).collect();
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
