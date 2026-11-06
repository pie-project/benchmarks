#if !canImport(PieServer)
// A build without pie; scripts/build-pie.sh supplies Vendor/pie/PieBuild.swift when it builds pie in.
enum PieBuild {
    static let commit: String? = nil
    static let unavailable = "pie is not built into this app (scripts/build-pie.sh builds PieServerCore.xcframework and the bench inferlet)"
}
#endif
