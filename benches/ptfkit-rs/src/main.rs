use std::error::Error;
use std::fs::File;
use std::hint::black_box;
use std::path::Path;
use std::time::Instant;

struct Arguments {
    dataset: String,
    warmups: usize,
    limit: Option<usize>,
}

fn parse_arguments() -> Result<Arguments, Box<dyn Error>> {
    let arguments: Vec<_> = std::env::args().skip(1).collect();
    if !(2..=3).contains(&arguments.len()) {
        return Err("usage: ptfkit-rs-benchmarks DATASET WARMUPS [LIMIT]".into());
    }
    Ok(Arguments {
        dataset: arguments[0].clone(),
        warmups: arguments[1].parse()?,
        limit: arguments.get(2).map(|value| value.parse()).transpose()?,
    })
}

fn load_array(dataset: &Path, name: &str) -> Result<Vec<f64>, Box<dyn Error>> {
    let file = File::open(dataset.join(format!("{name}.npy")))?;
    Ok(npyz::NpyFile::new(file)?.into_vec::<f64>()?)
}

fn print_record(case: &str, samples: usize, elapsed_ns: u128) {
    println!(
        r#"{{"target":"rust","case":"{case}","samples":{samples},"elapsed_ns":{elapsed_ns}}}"#
    );
}

fn observe(values: &[f64]) {
    black_box(values.iter().sum::<f64>());
}

fn main() -> Result<(), Box<dyn Error>> {
    let arguments = parse_arguments()?;
    let dataset = Path::new(&arguments.dataset);
    let sand = load_array(dataset, "sand")?;
    let silt = load_array(dataset, "silt")?;
    let clay = load_array(dataset, "clay")?;
    let bulk_density = load_array(dataset, "bulk_density")?;
    let organic_carbon = load_array(dataset, "organic_carbon")?;
    let samples = arguments.limit.unwrap_or(sand.len());
    let sand = &sand[..samples];
    let silt = &silt[..samples];
    let clay = &clay[..samples];
    let bulk_density = &bulk_density[..samples];
    let organic_carbon = &organic_carbon[..samples];

    let mut infiltration = vec![0.0; samples];
    for _ in 0..arguments.warmups {
        for index in 0..samples {
            infiltration[index] = ptfkit::dharumarajan2019::calc_ptf_dharumarajan2019_infiltration(
                sand[index],
                silt[index],
                clay[index],
            );
        }
        observe(&infiltration);
    }
    let started = Instant::now();
    for index in 0..samples {
        infiltration[index] = ptfkit::dharumarajan2019::calc_ptf_dharumarajan2019_infiltration(
            sand[index],
            silt[index],
            clay[index],
        );
    }
    let elapsed_ns = started.elapsed().as_nanos();
    observe(&infiltration);
    print_record("dharumarajan2019_infiltration", samples, elapsed_ns);

    let mut mayr_a_hc = vec![0.0; samples];
    let mut mayr_b_hc = vec![0.0; samples];
    let mut mayr_theta_s = vec![0.0; samples];
    for _ in 0..arguments.warmups {
        for index in 0..samples {
            let result = ptfkit::mayr1999::calc_ptf_mayr1999(
                sand[index],
                silt[index],
                clay[index],
                bulk_density[index],
                organic_carbon[index],
            );
            mayr_a_hc[index] = result.a_hc;
            mayr_b_hc[index] = result.b_hc;
            mayr_theta_s[index] = result.theta_s;
        }
        observe(&mayr_a_hc);
        observe(&mayr_b_hc);
        observe(&mayr_theta_s);
    }
    let started = Instant::now();
    for index in 0..samples {
        let result = ptfkit::mayr1999::calc_ptf_mayr1999(
            sand[index],
            silt[index],
            clay[index],
            bulk_density[index],
            organic_carbon[index],
        );
        mayr_a_hc[index] = result.a_hc;
        mayr_b_hc[index] = result.b_hc;
        mayr_theta_s[index] = result.theta_s;
    }
    let elapsed_ns = started.elapsed().as_nanos();
    observe(&mayr_a_hc);
    observe(&mayr_b_hc);
    observe(&mayr_theta_s);
    print_record("mayr1999", samples, elapsed_ns);

    let mut li_theta_s = vec![0.0; samples];
    let mut li_a_vg = vec![0.0; samples];
    let mut li_n_vg = vec![0.0; samples];
    let mut li_k_sat = vec![0.0; samples];
    for _ in 0..arguments.warmups {
        for index in 0..samples {
            let result = ptfkit::li2007::calc_ptf_li2007(
                sand[index],
                silt[index],
                clay[index],
                bulk_density[index],
                organic_carbon[index],
            );
            li_theta_s[index] = result.theta_s;
            li_a_vg[index] = result.a_vg;
            li_n_vg[index] = result.n_vg;
            li_k_sat[index] = result.k_sat;
        }
        observe(&li_theta_s);
        observe(&li_a_vg);
        observe(&li_n_vg);
        observe(&li_k_sat);
    }
    let started = Instant::now();
    for index in 0..samples {
        let result = ptfkit::li2007::calc_ptf_li2007(
            sand[index],
            silt[index],
            clay[index],
            bulk_density[index],
            organic_carbon[index],
        );
        li_theta_s[index] = result.theta_s;
        li_a_vg[index] = result.a_vg;
        li_n_vg[index] = result.n_vg;
        li_k_sat[index] = result.k_sat;
    }
    let elapsed_ns = started.elapsed().as_nanos();
    observe(&li_theta_s);
    observe(&li_a_vg);
    observe(&li_n_vg);
    observe(&li_k_sat);
    print_record("li2007", samples, elapsed_ns);
    Ok(())
}
