use inferlet::eta::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct Input {
    prompt_tokens: Vec<u32>,
    #[serde(default = "default_k")]
    k: usize,
}

fn default_k() -> usize {
    20
}

#[derive(Serialize)]
struct Output {
    ids: Vec<u32>,
    logprobs: Vec<f64>,
}

#[inferlet::main]
async fn main(input: Input) -> Result<Output> {
    inferlet::runtime::declare_restartable();
    if input.prompt_tokens.is_empty() {
        return Err("empty prompt".into());
    }
    let vocab = model::output_vocab_size();
    let n = input.prompt_tokens.len() as u32;
    let toks: Vec<i32> = input.prompt_tokens.iter().map(|&t| t as i32).collect();
    let toks = Channel::from(&toks[..]);
    let indptr = Channel::from([0u32, n]);
    let logits = Channel::new([vocab], dtype::f32);
    let ws = WorkingSet::new();
    let fwd = ForwardPass::new();
    fwd.embed(&toks, &indptr)?;
    fwd.state(&[&ws], StateGeometry::folding()).context("bind prefill state")?;
    fwd.epilogue(move || {
        logits.put(&reshape(intrinsics::output(0, "logits"), [vocab]));
    });
    let pipe = Pipeline::new();
    submit_frame(&pipe, &[Some(&fwd)]).context("prefill submit")?;
    let row = logits.take_host::<Vec<f32>>().await?;
    let max = row.iter().copied().fold(f32::NEG_INFINITY, f32::max) as f64;
    let lse = max + row.iter().map(|&x| (x as f64 - max).exp()).sum::<f64>().ln();
    let mut order: Vec<usize> = (0..row.len()).collect();
    let k = input.k.min(row.len());
    let rank = |a: &usize, b: &usize| row[*b].total_cmp(&row[*a]).then(a.cmp(b));
    order.select_nth_unstable_by(k.saturating_sub(1), rank);
    order.truncate(k);
    order.sort_by(rank);
    Ok(Output {
        ids: order.iter().map(|&i| i as u32).collect(),
        logprobs: order.iter().map(|&i| row[i] as f64 - lse).collect(),
    })
}
