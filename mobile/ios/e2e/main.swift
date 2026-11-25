import Foundation

@MainActor func main() async {
    let runner = Runner()
    guard let contract = runner.contract else { print("no workloads.json: \(runner.loadError ?? "")"); exit(1) }
    let env = ProcessInfo.processInfo.environment
    let ids = (env["PIEBENCH_MODELS"] ?? "llamacpp/qwen3.5-0.8b-llamacpp").split(separator: ",").map(String.init)
    let models = ids.compactMap { id in ModelEntry.all.first { $0.id == id } }
    let workloads = env["PIEBENCH_WORKLOADS"].map { $0.split(separator: ",").map(String.init) } ?? contract.workloads.map(\.id)
    await withCheckedContinuation { (done: CheckedContinuation<Void, Never>) in
        runner.start(RunPlan(models: models, workloads: workloads, tag: env["PIEBENCH_TAG"])) {
            if let url = env["PIEBENCH_POST"] {
                do { runner.say("POST: " + (try await Uploader.send(Storage.records, base: url, token: env["PIEBENCH_TOKEN"] ?? ""))) } catch {
                    runner.say("POST failed: \(error.localizedDescription)")
                }
            }
            runner.say("records: \(Storage.records.path)")
            done.resume()
        }
    }
}

await main()
