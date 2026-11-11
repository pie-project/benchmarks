use inferlet::chat;
use inferlet::eta::hybrid::prelude::*;
use inferlet::{model, monotonic_now_ns, session};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct Input {
    #[serde(default = "d_system")]
    system: String,
    #[serde(default = "d_max_tokens")]
    max_tokens: usize,
    #[serde(default = "d_k_max")]
    k_max: u32,
    #[serde(default = "d_draft_max")]
    draft_max: usize,
    #[serde(default)]
    think: bool,
}
fn d_system() -> String {
    "You are a helpful assistant. Answer clearly and concisely.".into()
}
fn d_max_tokens() -> usize {
    400
}
fn d_k_max() -> u32 {
    16
}
fn d_draft_max() -> usize {
    400
}

#[derive(Serialize)]
struct Output {
    answers: usize,
}

#[derive(Deserialize)]
struct Msg {
    op: String,
    #[serde(default)]
    text: String,
    #[serde(default)]
    n: usize,
    #[serde(default)]
    mode: String,
}

fn send(v: serde_json::Value) {
    session::send(&v.to_string());
}

fn now_ms() -> f64 {
    monotonic_now_ns() as f64 / 1e6
}

fn buffer_pages_for(survivors: u32, window: u32, page: u32) -> u32 {
    (page.saturating_sub(1) + survivors + window).div_ceil(page.max(1)).max(1)
}

#[allow(clippy::too_many_arguments)]
async fn fire(
    ws: &WorkingSet,
    rs: &[RsWorkingSet],
    pipeline: &Pipeline,
    tokens: &[u32],
    base: u32,
    fold: Option<u32>,
    buffer_pages: u32,
    page_size: u32,
) -> Result<Vec<u32>> {
    let rows = tokens.len() as u32;
    let total = base + rows;
    let pages = total.div_ceil(page_size);
    let ids = Channel::from_iter(tokens.iter().map(|&t| t as i32));
    let embed_indptr = Channel::from([0u32, rows]).named("embed_indptr");
    let positions = Channel::from_iter(base..total).named("positions");
    let page_list = Channel::from_iter(0..pages).named("pages");
    let page_indptr = Channel::from([0u32, pages]).named("page_indptr");
    let w_slot = Channel::from_iter((base..total).map(|p| p / page_size)).named("w_slot");
    let w_off = Channel::from_iter((base..total).map(|p| p % page_size)).named("w_off");
    let kv_len = Channel::from([total]).named("kv_len");
    let read_from = if fold.is_none() { rows - 1 } else { 0 };
    let readout = Channel::from_iter(read_from..rows).named("readout");
    let truth_out = Channel::new([rows - read_from], dtype::i32).named("truth");
    let fold_len = fold.map(|n| Channel::from([n]).named("fold_len"));

    let fwd = ForwardPass::new();
    fwd.embed(&ids, &embed_indptr)?;
    fwd.readout(&readout)?;
    fwd.attention(
        Some(KvBinding {
            working_set: ws,
            geometry: KvGeometry {
                readable_pages: ..,
                writable_pages: (base / page_size)..pages,
                kv_len: &kv_len,
                pages: &page_list,
                page_indptr: &page_indptr,
                w_slot: &w_slot,
                w_off: &w_off,
                positions: &positions,
                mask: None,
            },
        }),
        rs,
        RsGeometry {
            fold_len: fold_len.as_ref(),
            buffer: 0..buffer_pages,
        },
    )?;
    fwd.epilogue(move || {
        truth_out.put(reduce_argmax(intrinsics::logits()));
    });
    fwd.submit(pipeline).context("fire")?;
    Ok(truth_out
        .take_host::<Vec<i32>>()
        .await?
        .into_iter()
        .map(|t| t as u32)
        .collect())
}

struct Seq {
    ws: WorkingSet,
    rs: Vec<RsWorkingSet>,
    pipe: Pipeline,
    page_size: u32,
    rs_page: u32,
    fed: Vec<u32>,
    x: u32,
    base: u32,
    survivors: u32,
    out: Vec<u32>,
    done: bool,
}

impl Seq {
    fn new(max_pages: u32) -> Result<Self> {
        let ws = WorkingSet::new();
        ws.reserve(max_pages).context("reserve KV")?;
        Ok(Seq {
            ws,
            rs: vec![RsWorkingSet::new()],
            pipe: Pipeline::new(),
            page_size: kv_page_size(),
            rs_page: model::rs_buffer_page_size().max(1),
            fed: Vec::new(),
            x: 0,
            base: 0,
            survivors: 0,
            out: Vec::new(),
            done: false,
        })
    }

    async fn prefill(&mut self, toks: &[u32]) -> Result<Option<u32>> {
        if toks.is_empty() {
            return Ok(None);
        }
        let start = self.fed.len() as u32;
        let mut last = None;
        for (from, to) in prefill_chunks(toks.len() as u32, None) {
            let truth = fire(
                &self.ws,
                &self.rs,
                &self.pipe,
                &toks[from as usize..to as usize],
                start + from,
                None,
                0,
                self.page_size,
            )
            .await?;
            last = truth.last().copied();
        }
        self.fed.extend_from_slice(toks);
        Ok(last)
    }

    fn start_decode(&mut self, first: u32, stop: &[u32]) {
        self.x = first;
        self.base = self.fed.len() as u32;
        self.survivors = 0;
        self.out = vec![first];
        self.done = stop.contains(&first);
    }

    async fn step(&mut self, drafts: &[u32], stop: &[u32], max_out: usize) -> Result<(usize, Vec<u32>)> {
        let mut window = Vec::with_capacity(drafts.len() + 1);
        window.push(self.x);
        window.extend_from_slice(drafts);
        let w = window.len() as u32;
        let need = buffer_pages_for(self.survivors, w, self.rs_page);
        let have = self.rs[0].buffer_size();
        if have < need {
            self.rs[0]
                .alloc_buffer(need - have)
                .map_err(|why| format!("alloc rs buffer: {why}"))?;
        }
        let truth = fire(&self.ws, &self.rs, &self.pipe, &window, self.base, Some(self.survivors), need, self.page_size)
            .await?;
        let proposed = window.len() - 1;
        let mut m = 0usize;
        while m < proposed && window[m + 1] == truth[m] {
            m += 1;
        }
        let rejected = (proposed - m) as u32;
        if rejected > 0 {
            self.rs[0]
                .discard_buffered(rejected)
                .map_err(|why| format!("discard: {why}"))?;
        }
        let mut new = Vec::new();
        for &t in &window[1..=m] {
            new.push(t);
            if stop.contains(&t) || self.out.len() + new.len() >= max_out {
                self.done = true;
                break;
            }
        }
        if !self.done {
            let c = truth[m];
            new.push(c);
            if stop.contains(&c) || self.out.len() + new.len() >= max_out {
                self.done = true;
            }
            self.base += (m + 1) as u32;
            self.survivors = (m + 1) as u32;
            self.x = c;
        }
        self.out.extend_from_slice(&new);
        Ok((m, new))
    }
}

fn propose(out: &[u32], draft: &[u32], last: &mut usize, k: usize) -> (usize, Vec<u32>) {
    if draft.is_empty() || out.is_empty() {
        return (0, Vec::new());
    }
    for width in (1..=out.len().min(8)).rev() {
        let suffix = &out[out.len() - width..];
        let mut best: Option<usize> = None;
        for start in 0..draft.len().saturating_sub(width - 1) {
            if &draft[start..start + width] == suffix {
                let end = start + width;
                if best.is_none_or(|b| end.abs_diff(*last) < b.abs_diff(*last)) {
                    best = Some(end);
                }
            }
        }
        if let Some(end) = best {
            if end < draft.len() {
                *last = end;
                return (width, draft[end..(end + k).min(draft.len())].to_vec());
            }
        }
    }
    (0, Vec::new())
}

fn history_draft(tokens: &[u32], k: usize, max_ngram: usize) -> Vec<u32> {
    if tokens.len() < 2 {
        return Vec::new();
    }
    for width in (1..=max_ngram.min(tokens.len() - 1)).rev() {
        let suffix = &tokens[tokens.len() - width..];
        for start in (0..tokens.len() - width).rev() {
            if &tokens[start..start + width] == suffix {
                let from = start + width;
                let to = (from + k).min(tokens.len());
                if from < to {
                    return tokens[from..to].to_vec();
                }
            }
        }
    }
    Vec::new()
}

struct Template {
    system: String,
    think: bool,
}

impl Template {
    fn tokens(&self, text: &str) -> Vec<u32> {
        let mut t = chat::prefix();
        t.extend(chat::system(&self.system));
        t.extend(chat::user(text));
        let cue = chat::cue();
        let cue_text = model::decode(&cue).unwrap_or_default();
        t.extend(cue);
        if !self.think {
            if cue_text.trim_end().ends_with("<think>") {
                t.extend(model::encode("\n\n</think>\n\n"));
            } else if !cue_text.contains("<think>") {
                t.extend(model::encode("<think>\n\n</think>\n\n"));
            }
        }
        t
    }
}

#[inferlet::main]
async fn main(input: Input) -> Result<Output> {
    let tpl = Template { system: input.system.clone(), think: input.think };
    let stop = chat::stop_tokens();
    let page_size = kv_page_size();
    let max_pages = (4096 + input.max_tokens.max(input.draft_max) as u32 + 64).div_ceil(page_size);

    let a = tpl.tokens("hello there");
    let b = tpl.tokens("hello there general kenobi");
    let common = a.iter().zip(&b).take_while(|(x, y)| x == y).count();
    let unstable = a.len() - common + 1;
    let stable = |text: &str| -> Vec<u32> {
        let t = tpl.tokens(text);
        t[..t.len().saturating_sub(unstable)].to_vec()
    };
    send(serde_json::json!({"ev": "ready", "unstable_tail": unstable}));

    let mut trunk = Seq::new(max_pages)?;
    let mut lane: Option<(String, Seq)> = None;
    let mut answers = 0usize;

    while let Some(raw) = session::receive().await {
        let msg: Msg = match serde_json::from_str(&raw) {
            Ok(m) => m,
            Err(e) => {
                send(serde_json::json!({"ev": "error", "why": e.to_string()}));
                continue;
            }
        };
        match msg.op.as_str() {
            "text" => {
                let t0 = now_ms();
                let st = stable(&msg.text);
                if !st.starts_with(&trunk.fed) {
                    trunk = Seq::new(max_pages)?;
                }
                let rest = st[trunk.fed.len()..].to_vec();
                trunk.prefill(&rest).await?;
                send(serde_json::json!({"ev": "fed", "n": trunk.fed.len(), "new": rest.len(), "ms": now_ms() - t0}));
            }
            "draft" => {
                let t0 = now_ms();
                if lane.as_ref().is_none_or(|(t, _)| *t != msg.text) {
                    let full = tpl.tokens(&msg.text);
                    let mut s = Seq::new(max_pages)?;
                    let first = s.prefill(&full).await?.expect("a prompt");
                    s.start_decode(first, &stop);
                    lane = Some((msg.text.clone(), s));
                }
                let (_, s) = lane.as_mut().expect("lane");
                let n = msg.n.max(1);
                for _ in 0..n {
                    if s.done || s.out.len() >= input.draft_max {
                        break;
                    }
                    s.step(&[], &stop, input.draft_max).await?;
                }
                let preview = model::decode(&s.out).unwrap_or_default();
                send(serde_json::json!({"ev": "drafted", "n": s.out.len(), "done": s.done,
                    "ms": now_ms() - t0, "preview": preview}));
            }
            "enter" => {
                let plain = msg.mode == "plain";
                let no_drafts = plain || msg.mode == "prefill";
                let t0 = now_ms();
                let full = tpl.tokens(&msg.text);
                if plain || !full.starts_with(&trunk.fed) {
                    trunk = Seq::new(max_pages)?;
                }
                let reused = trunk.fed.len();
                let rest = full[reused..].to_vec();
                let first = trunk.prefill(&rest).await?.expect("a prompt");
                trunk.start_decode(first, &stop);
                let ttft = now_ms() - t0;
                let draft: Vec<u32> = match (&lane, plain) {
                    (Some((_, s)), false) => s.out.clone(),
                    _ => Vec::new(),
                };
                let mut shown = String::new();
                let stream = |out: &[u32], shown: &mut String| {
                    let text = model::decode(out).unwrap_or_default();
                    if text.len() > shown.len() && text.starts_with(shown.as_str()) {
                        send(serde_json::json!({"ev": "tok", "t": &text[shown.len()..]}));
                        *shown = text;
                    } else if text != *shown {
                        send(serde_json::json!({"ev": "tok", "reset": true, "t": text}));
                        *shown = text;
                    }
                };
                stream(&trunk.out, &mut shown);
                let (mut rounds, mut accepted, mut drafted) = (0usize, 0usize, 0usize);
                let mut last = 0usize;
                while !trunk.done && trunk.out.len() < input.max_tokens {
                    let drafts = if no_drafts {
                        Vec::new()
                    } else {
                        let (width, d) = propose(&trunk.out, &draft, &mut last, input.k_max as usize);
                        if width >= 2 || (width == 1 && trunk.out.len() == 1) {
                            d
                        } else if width == 1 {
                            d.into_iter().take(4).collect()
                        } else {
                            let mut hist = full.clone();
                            hist.extend_from_slice(&trunk.out);
                            history_draft(&hist, 3, 3)
                        }
                    };
                    drafted += drafts.len();
                    let (m, _) = trunk.step(&drafts, &stop, input.max_tokens).await?;
                    accepted += m;
                    rounds += 1;
                    stream(&trunk.out, &mut shown);
                }
                let total = now_ms() - t0;
                answers += 1;
                send(serde_json::json!({"ev": "done", "mode": msg.mode.clone(),
                    "prefill_ms": ttft, "prefilled_at_enter": full.len() - reused,
                    "ttft_ms": ttft, "total_ms": total, "tokens": trunk.out.len(),
                    "prompt_tokens": full.len(), "prefilled_while_typing": reused,
                    "rounds": rounds, "accepted_from_draft": accepted, "drafted": drafted,
                    "draft_len": draft.len()}));
                trunk = Seq::new(max_pages)?;
                lane = None;
            }
            "quit" => break,
            other => send(serde_json::json!({"ev": "error", "why": format!("unknown op {other}")})),
        }
    }
    trunk.pipe.close();
    Ok(Output { answers })
}
