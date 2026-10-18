import SwiftUI

struct ContentView: View {
    @StateObject private var ble = BLEManager()
    var body: some View {
        NavigationStack {
            Form {
                Section("蓝牙连接") {
                    Text(ble.bluetoothStatus).font(.caption).foregroundStyle(.secondary)
                    Text(ble.status)
                    if let name = ble.connectedName {
                        Label(name, systemImage: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                    }
                    if ble.scanSecondsRemaining > 0 {
                        Text("扫描倒计时：\(ble.scanSecondsRemaining) 秒")
                            .monospacedDigit()
                            .foregroundStyle(.blue)
                    }
                    // Form's automatic button style can activate both buttons in a row.
                    // Explicit borderless styling gives each control its own hit target.
                    HStack {
                        Button("扫描") { ble.scan() }.disabled(ble.active)
                        Spacer()
                        Button("断开 / 停止") { ble.disconnect() }
                    }
                    .buttonStyle(.borderless)
                    ForEach(ble.devices, id: \.identifier) { device in
                        Button(device.name ?? device.identifier.uuidString) { ble.connect(device) }
                            .disabled(ble.active)
                    }
                }
                Section("发送文本") {
                    TextEditor(text: $ble.text).frame(minHeight: 100)
                    Text("\(ble.text.utf8.count) / 512 UTF-8 字节").font(.caption)
                    Button(ble.busy ? "等待回传…" : "发送") { ble.send(ble.text) }
                        .disabled(!ble.ready || ble.busy || ble.text.utf8.count > 512)
                }
                Section("收发记录") {
                    ForEach(Array(ble.messages.enumerated()), id: \.offset) { _, message in
                        Text(message).font(.system(.body, design: .monospaced)).textSelection(.enabled)
                    }
                }
            }
            .navigationTitle("XIAO 蓝牙文本")
        }
    }
}
