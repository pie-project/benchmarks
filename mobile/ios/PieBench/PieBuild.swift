#if !canImport(PieServer)
enum PieBuild {
    static let commit: String? = nil
    static let unavailable = "pie is not built into this app (scripts/build-pie.sh builds PieServerCore.xcframework and the bench inferlet)"
}
#endif
