import SwiftUI

@main
struct PieBenchApp: App {
    @StateObject private var runner = Runner()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(runner)
                .task { await AutoRun.maybeStart(runner) }
        }
    }
}

enum AutoRun {
    static func value(_ key: String) -> String? {
        if let v = ProcessInfo.processInfo.environment[key], !v.isEmpty { return v }
        return UserDefaults.standard.string(forKey: key)
    }

    @MainActor static func maybeStart(_ runner: Runner) async {
        guard value("PIEBENCH_AUTORUN") == "1", let contract = runner.contract else { return }
        let ids = (value("PIEBENCH_MODELS") ?? "llamacpp/qwen3.5-0.8b-llamacpp").split(separator: ",").map(String.init)
        let models = ids.compactMap { id in ModelEntry.all.first { $0.id == id } }
        let workloads = value("PIEBENCH_WORKLOADS").map { $0.split(separator: ",").map(String.init) } ?? contract.workloads.map(\.id)
        runner.say("autorun: \(ids) \(workloads)")
        runner.start(RunPlan(models: models, workloads: workloads, tag: value("PIEBENCH_TAG"))) {
            if let url = value("PIEBENCH_POST") {
                do { runner.say("POST: " + (try await Uploader.send(Storage.records, base: url, token: value("PIEBENCH_TOKEN") ?? ""))) } catch {
                    runner.say("POST failed: \(error.localizedDescription)")
                }
            }
            runner.say("autorun finished: \(Storage.records.path)")
            if value("PIEBENCH_EXIT") == "1" { exit(0) }
        }
    }
}
