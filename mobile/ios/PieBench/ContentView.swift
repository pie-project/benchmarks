import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @EnvironmentObject var runner: Runner
    @AppStorage("engines") private var enginesCSV = "llamacpp,pie"
    @AppStorage("models") private var modelsCSV = "llamacpp/qwen3.5-0.8b-llamacpp,pie/qwen3.5-0.8b-mlx4"
    @AppStorage("workloads") private var workloadsCSV = "raw-512-256,c4,pf4-512"
    @AppStorage("tag") private var tag = ""
    @State private var showSettings = false
    @State private var importing: ModelEntry?
    @State private var refresh = 0

    private func set(_ csv: String) -> Set<String> { Set(csv.split(separator: ",").map(String.init)) }
    private func toggle(_ binding: Binding<String>, _ id: String) -> Binding<Bool> {
        Binding(get: { set(binding.wrappedValue).contains(id) }, set: { on in
            var s = set(binding.wrappedValue)
            if on { s.insert(id) } else { s.remove(id) }
            binding.wrappedValue = s.sorted().joined(separator: ",")
        })
    }

    private var selectedModels: [ModelEntry] {
        let e = set(enginesCSV), m = set(modelsCSV)
        return ModelEntry.all.filter { e.contains($0.engine.rawValue) && m.contains($0.id) }
    }

    var body: some View {
        NavigationStack {
            List {
                deviceSection
                Section("Engines") {
                    ForEach(EngineID.allCases) { e in
                        Toggle(isOn: toggle($enginesCSV, e.rawValue)) {
                            VStack(alignment: .leading) {
                                Text(e.label)
                                if let m = ModelEntry.all.first(where: { $0.engine == e }), let r = Engines.adapter(e).unsupportedReason(m) {
                                    Text(r).font(.caption2).foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }
                Section("Models") {
                    ForEach(ModelEntry.all.filter { set(enginesCSV).contains($0.engine.rawValue) }) { m in
                        HStack {
                            Toggle(isOn: toggle($modelsCSV, m.id)) {
                                VStack(alignment: .leading) {
                                    Text(m.artifact).font(.callout)
                                    Text("\(m.engine.label) · \(String(format: "%.2f GB", Double(m.bytes) / 1e9)) · \(Downloader.present(m) != nil ? "on phone" : "downloads on Run")")
                                        .font(.caption2).foregroundStyle(.secondary)
                                }
                            }
                            Button { importing = m } label: { Image(systemName: "square.and.arrow.down") }
                                .buttonStyle(.borderless)
                        }
                    }
                    .id(refresh)
                }
                Section("Workloads") {
                    ForEach(runner.contract?.workloads ?? []) { w in
                        Toggle(isOn: toggle($workloadsCSV, w.id)) {
                            Text("\(w.id)  ·  \(w.concurrency) at once, \(w.prefill) in / \(w.decode) out")
                        }
                    }
                }
                Section {
                    if runner.running {
                        Button("Stop", role: .destructive) { runner.stop() }
                        Text(runner.status).font(.caption)
                        if let p = runner.downloadProgress { ProgressView(value: p) }
                    } else {
                        Button("Run \(selectedModels.count) model(s)") {
                            let wl = (runner.contract?.workloads ?? []).map(\.id).filter { set(workloadsCSV).contains($0) }
                            runner.start(RunPlan(models: selectedModels, workloads: wl, tag: tag.isEmpty ? nil : tag)) { refresh += 1 }
                        }
                        .disabled(selectedModels.isEmpty || runner.contract == nil)
                    }
                }
                resultsSection
                Section("Log") {
                    ScrollView {
                        Text(runner.log.suffix(200).joined(separator: "\n"))
                            .font(.system(.caption2, design: .monospaced))
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                    }
                    .frame(minHeight: 160, maxHeight: 320)
                }
            }
            .navigationTitle("Pie Bench")
            .toolbar { Button { showSettings = true } label: { Image(systemName: "gear") } }
            .sheet(isPresented: $showSettings) { SettingsView(tag: $tag) }
            .fileImporter(isPresented: Binding(get: { importing != nil }, set: { if !$0 { importing = nil } }),
                          allowedContentTypes: [.item, .folder]) { result in
                guard let m = importing, case .success(let url) = result else { return }
                do { try Downloader.importItem(url, for: m); runner.say("imported \(url.lastPathComponent) as \(m.artifact)") } catch {
                    runner.say("import failed: \(error.localizedDescription)")
                }
                refresh += 1
            }
        }
    }

    private var deviceSection: some View {
        Section("Device") {
            LabeledContent("Model", value: "\(DeviceInfo.machine)\(DeviceInfo.soc.map { " · \($0)" } ?? "")")
            LabeledContent("GPU", value: DeviceInfo.gpu ?? "?")
            LabeledContent("RAM", value: String(format: "%.1f GiB · app may use %.1f GiB", DeviceInfo.ramGiB, Double(DeviceInfo.availableBytes) / 1_073_741_824))
            LabeledContent("iOS", value: "\(DeviceInfo.osVersion) · thermal \(DeviceInfo.thermal)\(DeviceInfo.isSimulator ? " · simulator" : "")")
            if let e = runner.loadError { Text(e).foregroundStyle(.red) }
        }
    }

    private var resultsSection: some View {
        Section("Results (display only)") {
            if runner.rows.isEmpty { Text("No rows yet").foregroundStyle(.secondary) }
            ForEach(runner.rows) { r in
                VStack(alignment: .leading, spacing: 2) {
                    Text("\(r.artifact) · \(r.workload)").font(.callout)
                    if r.status == "pass" {
                        Text(String(format: "decode %.1f tok/s · prefill %.0f tok/s · TTFT %.3fs · peak %.2f GiB",
                                    r.decodeTokS ?? 0, r.prefillTokS ?? 0, r.ttftS ?? 0, r.peakGiB ?? 0))
                            .font(.caption.monospacedDigit())
                    } else {
                        Text("\(r.status): \(r.error ?? "")").font(.caption).foregroundStyle(r.status == "fail" ? .red : .secondary)
                    }
                }
            }
            ShareLink(item: Storage.records) { Label("Share records.jsonl", systemImage: "square.and.arrow.up") }
                .disabled(runner.running)
        }
    }
}

struct SettingsView: View {
    @Binding var tag: String
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section(footer: Text("Empty = the tag chosen at import.")) {
                    TextField("Tag", text: $tag).textInputAutocapitalization(.never).autocorrectionDisabled()
                }
                Section(footer: Text("Pie models download on Run from Hugging Face (\(Downloader.pieRepo)); to use your own, tap the import button next to the model and pick its .metal.zt, or put <artifact>.metal.zt in Files › On My iPhone › Pie Bench › models.")) {
                    LabeledContent("records.jsonl", value: "Files › Pie Bench")
                }
            }
            .navigationTitle("Settings")
            .toolbar { Button("Done") { dismiss() } }
        }
    }
}
