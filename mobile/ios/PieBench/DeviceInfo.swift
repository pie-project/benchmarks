import Foundation
import Metal
#if canImport(UIKit)
import UIKit
#endif
import os

enum DeviceInfo {
    static var machine: String {
        #if targetEnvironment(simulator)
        if let m = ProcessInfo.processInfo.environment["SIMULATOR_MODEL_IDENTIFIER"] { return m }
        #endif
        var u = utsname()
        uname(&u)
        return withUnsafeBytes(of: &u.machine) { String(decoding: $0.prefix { $0 != 0 }, as: UTF8.self) }
    }

    static var isSimulator: Bool {
        #if targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }

    static let socTable: [String: String] = [
        "iPhone14,2": "A15 Bionic", "iPhone14,3": "A15 Bionic", "iPhone14,4": "A15 Bionic", "iPhone14,5": "A15 Bionic",
        "iPhone14,6": "A15 Bionic", "iPhone14,7": "A15 Bionic", "iPhone14,8": "A15 Bionic",
        "iPhone15,2": "A16 Bionic", "iPhone15,3": "A16 Bionic", "iPhone15,4": "A16 Bionic", "iPhone15,5": "A16 Bionic",
        "iPhone16,1": "A17 Pro", "iPhone16,2": "A17 Pro",
        "iPhone17,1": "A18 Pro", "iPhone17,2": "A18 Pro", "iPhone17,3": "A18", "iPhone17,4": "A18", "iPhone17,5": "A18",
        "iPhone18,1": "A19 Pro", "iPhone18,2": "A19 Pro", "iPhone18,3": "A19", "iPhone18,4": "A19 Pro",
        "iPad16,1": "A17 Pro", "iPad16,2": "A17 Pro",
        "iPad16,3": "M4", "iPad16,4": "M4", "iPad16,5": "M4", "iPad16,6": "M4",
        "iPad17,1": "M5", "iPad17,2": "M5", "iPad17,3": "M5", "iPad17,4": "M5",
    ]

    static var soc: String? { socTable[machine] }
    static var gpu: String? { MTLCreateSystemDefaultDevice()?.name }
    static var ramGiB: Double { Double(ProcessInfo.processInfo.physicalMemory) / 1_073_741_824 }
    static var cores: Int { ProcessInfo.processInfo.processorCount }
    static var osVersion: String {
        #if canImport(UIKit)
        return UIDevice.current.systemVersion
        #else
        let v = ProcessInfo.processInfo.operatingSystemVersion
        return "macOS \(v.majorVersion).\(v.minorVersion)"
        #endif
    }

    static var thermal: String {
        switch ProcessInfo.processInfo.thermalState {
        case .nominal: return "nominal"
        case .fair: return "fair"
        case .serious: return "serious"
        case .critical: return "critical"
        @unknown default: return "unknown"
        }
    }

    @MainActor static var battery: (pct: Int?, charging: Bool?) {
        #if !canImport(UIKit)
        return (nil, nil)
        #else
        UIDevice.current.isBatteryMonitoringEnabled = true
        let level = UIDevice.current.batteryLevel
        let state = UIDevice.current.batteryState
        let pct = level < 0 ? nil : Int((level * 100).rounded())
        let charging: Bool? = state == .unknown ? nil : (state == .charging || state == .full)
        return (pct, charging)
        #endif
    }

    static var availableBytes: Int64 {
        #if os(iOS)
        return Int64(os_proc_available_memory())
        #else
        return 0
        #endif
    }

    @MainActor static func json(thermalStart: String, thermalEnd: String) -> J {
        let b = battery
        return .obj([
            ("os", .str("ios")), ("os_version", .str(osVersion)), ("manufacturer", .str("Apple")),
            ("model", .str(machine)), ("device", .str(machine)), ("soc", .opt(soc)), ("soc_vendor", .str("Apple")),
            ("gpu", .opt(gpu)), ("ram_gib", .num((ramGiB * 100).rounded() / 100)), ("cpu_cores", .int(cores)),
            ("abi", .str("arm64")), ("emulator", .bool(isSimulator)),
            ("thermal_start", .str(thermalStart)), ("thermal_end", .str(thermalEnd)),
            ("battery_pct", .opt(b.pct)), ("charging", b.charging.map(J.bool) ?? .null),
        ])
    }
}

enum Memory {
    static func footprint() -> (current: UInt64, peak: UInt64) {
        var info = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size / MemoryLayout<natural_t>.size)
        let kr = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        guard kr == KERN_SUCCESS else { return (0, 0) }
        return (info.phys_footprint, UInt64(max(0, info.ledger_phys_footprint_peak)))
    }
}

final class MemorySampler: @unchecked Sendable {
    private var peak: UInt64 = 0
    private let lock = NSLock()
    private var timer: DispatchSourceTimer?

    func start() {
        peak = Memory.footprint().current
        let t = DispatchSource.makeTimerSource(queue: .global(qos: .utility))
        t.schedule(deadline: .now(), repeating: .milliseconds(25))
        t.setEventHandler { [weak self] in
            let c = Memory.footprint().current
            guard let self else { return }
            self.lock.lock(); if c > self.peak { self.peak = c }; self.lock.unlock()
        }
        t.resume()
        timer = t
    }

    func stop() -> Double {
        timer?.cancel()
        timer = nil
        let c = Memory.footprint().current
        lock.lock(); let p = max(peak, c); lock.unlock()
        return Double(p) / 1_073_741_824
    }
}
