import Foundation

indirect enum J {
    case null
    case bool(Bool)
    case int(Int)
    case num(Double)
    case str(String)
    case arr([J])
    case obj([(String, J)])

    static func opt(_ s: String?) -> J { s.map(J.str) ?? .null }
    static func opt(_ d: Double?) -> J { d.map(J.num) ?? .null }
    static func opt(_ i: Int?) -> J { i.map(J.int) ?? .null }

    var text: String {
        var out = ""
        write(&out)
        return out
    }

    private func write(_ out: inout String) {
        switch self {
        case .null: out += "null"
        case .bool(let b): out += b ? "true" : "false"
        case .int(let i): out += String(i)
        case .num(let d):
            if !d.isFinite { out += "null" } else if d == d.rounded() && abs(d) < 1e15 { out += String(format: "%.1f", d) } else { out += String(d) }
        case .str(let s): Self.quote(s, &out)
        case .arr(let a):
            out += "["
            for (i, v) in a.enumerated() { if i > 0 { out += "," }; v.write(&out) }
            out += "]"
        case .obj(let o):
            out += "{"
            for (i, (k, v)) in o.enumerated() {
                if i > 0 { out += "," }
                Self.quote(k, &out); out += ":"; v.write(&out)
            }
            out += "}"
        }
    }

    private static func quote(_ s: String, _ out: inout String) {
        out += "\""
        for u in s.unicodeScalars {
            switch u {
            case "\"": out += "\\\""
            case "\\": out += "\\\\"
            case "\n": out += "\\n"
            case "\r": out += "\\r"
            case "\t": out += "\\t"
            default:
                if u.value < 0x20 { out += String(format: "\\u%04x", u.value) } else { out.unicodeScalars.append(u) }
            }
        }
        out += "\""
    }

    static func parse(_ line: String) -> [String: Any]? {
        guard let d = line.data(using: .utf8) else { return nil }
        return (try? JSONSerialization.jsonObject(with: d)) as? [String: Any]
    }
}
