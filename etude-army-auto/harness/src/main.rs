use army_auto::army;
use std::{env, path::Path, process::ExitCode};

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let Some(options) = army::options(&args) else {
        eprintln!("army-auto: bad arguments");
        return ExitCode::from(2);
    };
    let var = |name: &str| env::var(name).unwrap_or_default();
    let endpoint = army::Endpoint {
        base_url: var("ARMY_BASE_URL"),
        key_file: var("ARMY_KEY_FILE"),
        model: var("ARMY_MODEL"),
        context: var("ARMY_CONTEXT").parse().unwrap_or(65_536),
        output: 8192,
        compaction: 37_089,
        reasoning: true,
        lanes: var("ARMY_LANES").parse().unwrap_or(9),
    };
    match army::run(
        &options,
        &endpoint,
        Path::new(&var("ARMY_AGENT")),
        &mut std::io::stdout(),
    ) {
        Ok(true) => ExitCode::SUCCESS,
        Ok(false) => ExitCode::from(1),
        Err(cause) => {
            eprintln!("army: {cause}");
            ExitCode::from(2)
        }
    }
}
