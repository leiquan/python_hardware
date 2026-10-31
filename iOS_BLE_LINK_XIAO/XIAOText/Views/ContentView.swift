import SwiftUI

struct ContentView: View {
    @StateObject private var ble = BLEManager()
    @State private var throttle = 0.0
    @Environment(\.scenePhase) private var scenePhase
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
                Section("ESC 协议原型 · 仅模拟") {
                    Text("模式：\(ble.controlMode) · 状态：\(ble.controlState)")
                    Text("板端油门：\(ble.actualThrottle) / 1000")
                    Text("每次手动发送只维持 1.5 秒；无自动续期。未适配真实电调。")
                        .font(.caption)
                    Slider(value: $throttle, in: 0...1000, step: 1)
                    Text("待发送：\(Int(throttle)) / 1000")
                    Button("零油门解锁 ARM") { throttle = 0; ble.control("ARM", throttle: 0) }
                        .disabled(!ble.ready || ble.busy || ble.controlMode != "simulation" || ble.controlState != "DISARMED")
                    Button("发送油门 / 续期") { ble.control("SET_THROTTLE", throttle: Int(throttle)) }
                        .disabled(!ble.ready || ble.busy || ble.controlMode != "simulation" || ble.controlState != "ARMED")
                    Button("停机 DISARM") { throttle = 0; ble.control("DISARM") }
                        .disabled(!ble.ready || ble.busy)
                    Button("紧急停机 ESTOP", role: .destructive) { throttle = 0; ble.control("ESTOP") }
                        .disabled(!ble.ready)
                    Button("清除急停（仍保持未解锁）") { throttle = 0; ble.control("RESET_ESTOP") }
                        .disabled(!ble.ready || ble.busy || ble.controlState != "ESTOP")
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
            .onChange(of: scenePhase) { phase in
                if phase != .active { throttle = 0; ble.disconnect() }
            }
            .navigationTitle("XIAO 蓝牙文本")
        }
    }
}
