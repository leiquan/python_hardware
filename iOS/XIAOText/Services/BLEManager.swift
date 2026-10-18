import Foundation
import Combine
import CoreBluetooth

// CBCentralManager callbacks and UI updates run on the main queue.
final class BLEManager: NSObject, ObservableObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    static let serviceID = CBUUID(string: "A8E00001-9D4B-4F2A-A8A6-6C33F8D11E01")
    static let rxID = CBUUID(string: "A8E00002-9D4B-4F2A-A8A6-6C33F8D11E01")
    static let txID = CBUUID(string: "A8E00003-9D4B-4F2A-A8A6-6C33F8D11E01")
    @Published var text = "你好 XIAO!"
    @Published var bluetoothStatus = "蓝牙：初始化中"
    @Published var status = "正在初始化蓝牙"
    @Published var devices: [CBPeripheral] = []
    @Published var messages: [String] = []
    @Published var ready = false
    @Published var busy = false
    @Published var connectedName: String?
    @Published var active = false
    @Published var scanSecondsRemaining = 0
    private var central: CBCentralManager!
    private var peer: CBPeripheral?
    private var rx: CBCharacteristic?
    private var tx: CBCharacteristic?
    private var chunks: [Data] = []
    private var incoming = Data()
    private var nextID = 0
    private var pendingID: Int?
    private var deadline: DispatchWorkItem?
    private var discoveredIDs = Set<UUID>()
    private var scanDeadline: DispatchWorkItem?
    private var scanTimer: Timer?

    private func stopScan() {
        scanDeadline?.cancel()
        scanDeadline = nil
        scanTimer?.invalidate()
        scanTimer = nil
        scanSecondsRemaining = 0
        if central.state == .poweredOn { central.stopScan() }
    }

    override init() {
        super.init()
        central = CBCentralManager(delegate: self, queue: .main)
    }
    private func log(_ text: String) {
        messages.append(text)
        if messages.count > 100 { messages.removeFirst(messages.count - 100) }
    }
    private func timeout(_ seconds: Double, action: @escaping () -> Void) {
        deadline?.cancel()
        let item = DispatchWorkItem(block: action)
        deadline = item
        DispatchQueue.main.asyncAfter(deadline: .now() + seconds, execute: item)
    }
    private func clearSession() {
        deadline?.cancel(); deadline = nil
        connectedName = nil
        ready = false; busy = false
        rx = nil; tx = nil; chunks = []; incoming.removeAll(); pendingID = nil
    }
    private func fail(_ message: String) {
        log(message); status = message
        disconnect(keepStatus: true)
    }
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        switch central.state {
        case .poweredOn: status = "蓝牙已开启，点击扫描"
        case .poweredOff: status = "请开启 iPhone 蓝牙"
        case .unauthorized: status = "请在设置 → 隐私与安全性 → 蓝牙中允许此 App"
        case .unsupported: status = "此设备不支持 BLE；请使用真实 iPhone"
        case .resetting: status = "蓝牙正在重置"
        default: status = "蓝牙状态未知"
        }
        bluetoothStatus = "蓝牙状态：" + bluetoothStateDescription()
        log(bluetoothStatus)
        if central.state != .poweredOn {
            stopScan(); clearSession(); active = false; peer = nil; devices = []
        }
    }
    private func bluetoothStateDescription() -> String {
        switch central.state {
        case .poweredOn: return "已开启"
        case .poweredOff: return "已关闭，请到系统设置开启蓝牙"
        case .unauthorized: return "未授权，请在设置 → 隐私与安全性 → 蓝牙中允许 XIAOText"
        case .unsupported: return "设备不支持，请使用真实 iPhone"
        case .resetting: return "系统正在重置蓝牙，请稍后重试"
        default: return "尚未就绪，请稍后重试"
        }
    }
    func scan() {
        guard central.state == .poweredOn else {
            status = "无法扫描：" + bluetoothStateDescription()
            bluetoothStatus = "蓝牙状态：" + bluetoothStateDescription()
            log(status)
            return
        }
        guard !active else {
            status = "正在连接或已连接，请先点断开 / 停止"
            log(status)
            return
        }
        stopScan()
        devices = []
        messages.removeAll()
        scanSecondsRemaining = 15
        status = "正在扫描附近设备"
        let endTime = ProcessInfo.processInfo.systemUptime + 15
        scanTimer = Timer(timeInterval: 0.2, repeats: true) { [weak self] _ in
            self?.scanSecondsRemaining = max(0, Int(ceil(endTime - ProcessInfo.processInfo.systemUptime)))
        }
        RunLoop.main.add(scanTimer!, forMode: .common)
        discoveredIDs.removeAll()
        log("开始扫描附近 BLE 设备，按 UUID 或 XIAO-Text 名称识别")
        central.scanForPeripherals(withServices: nil, options: [CBCentralManagerScanOptionAllowDuplicatesKey: true])
        let item = DispatchWorkItem { [weak self] in
            guard let self = self else { return }
            self.stopScan()
            if !self.active { self.status = self.devices.isEmpty ? "发现 \(self.discoveredIDs.count) 个 BLE 设备，未识别到 XIAO；请查看下方记录" : "选择设备连接" }
        }
        scanDeadline = item
        DispatchQueue.main.asyncAfter(deadline: .now() + 15, execute: item)
    }
    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral,
                        advertisementData: [String: Any], rssi RSSI: NSNumber) {
        guard central.isScanning, !active else { return }
        let name = advertisementData[CBAdvertisementDataLocalNameKey] as? String ?? peripheral.name ?? "未命名"
        let services = (advertisementData[CBAdvertisementDataServiceUUIDsKey] as? [CBUUID] ?? [])
            + (advertisementData[CBAdvertisementDataOverflowServiceUUIDsKey] as? [CBUUID] ?? [])
        if discoveredIDs.insert(peripheral.identifier).inserted {
            log("发现：\(name)，RSSI \(RSSI)，服务：\(services.map { $0.uuidString }.joined(separator: ", "))")
        }
        // The board advertises XIAO in its primary packet and XIAO-Text in scan response.
        // Still verify the custom GATT service before enabling text transmission.
        let knownNames = ["XIAO", "XIAO-Text"]
        let matches = services.contains(Self.serviceID) || knownNames.contains(name)
            || knownNames.contains(peripheral.name ?? "")
        if matches, !devices.contains(where: { $0.identifier == peripheral.identifier }) {
            devices.append(peripheral)
            status = "已找到 XIAO，点击设备连接"
            log("识别到 XIAO：\(name)")
        }
    }
    func connect(_ peripheral: CBPeripheral) {
        guard !active, central.state == .poweredOn else { return }
        stopScan(); clearSession()
        active = true; peer = peripheral; peripheral.delegate = self
        status = "正在连接 \(peripheral.name ?? "XIAO")"
        central.connect(peripheral, options: nil)
        timeout(15) { [weak self] in self?.fail("连接或服务发现超时，请重新扫描") }
    }
    func disconnect() { disconnect(keepStatus: false) }
    private func disconnect(keepStatus: Bool) {
        stopScan(); clearSession()
        let previousPeer = peer
        peer = nil
        active = false
        previousPeer?.delegate = nil
        if let previousPeer = previousPeer {
            central.cancelPeripheralConnection(previousPeer)
        }
        if !keepStatus {
            status = central.state == .poweredOn
                ? "已停止，可以点击扫描"
                : "已停止；" + bluetoothStateDescription()
        }
    }
    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        guard peer === peripheral else { return }
        status = "正在发现文本服务"
        peripheral.discoverServices([Self.serviceID])
    }
    func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        guard peer === peripheral else { return }
        clearSession(); peer = nil; active = false
        status = "连接失败：\(error?.localizedDescription ?? "未知原因")"
    }
    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        guard peer === peripheral else { return }
        let hadPending = busy
        clearSession(); peer = nil; active = false
        if hadPending { log("连接中断，本次消息未确认；重连后手动发送") }
        if let error = error { status = "连接断开：\(error.localizedDescription)" }
        else if !status.contains("超时") { status = "已断开，可重新扫描连接" }
    }
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard peer === peripheral else { return }
        guard error == nil, let service = peripheral.services?.first(where: { $0.uuid == Self.serviceID }) else {
            fail("找不到文本服务：\(error?.localizedDescription ?? "UUID 不匹配")"); return
        }
        peripheral.discoverCharacteristics([Self.rxID, Self.txID], for: service)
    }
    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        guard peer === peripheral else { return }
        guard error == nil else { fail("发现特征失败"); return }
        rx = service.characteristics?.first(where: { $0.uuid == Self.rxID })
        tx = service.characteristics?.first(where: { $0.uuid == Self.txID })
        guard let rx = rx, let tx = tx, rx.properties.contains(.write), tx.properties.contains(.notify) else {
            fail("缺少 Write / Notify 特征"); return
        }
        peripheral.setNotifyValue(true, for: tx)
    }
    func peripheral(_ peripheral: CBPeripheral, didUpdateNotificationStateFor characteristic: CBCharacteristic, error: Error?) {
        guard peer === peripheral, characteristic.uuid == Self.txID else { return }
        guard error == nil, characteristic.isNotifying else { fail("订阅回传失败"); return }
        deadline?.cancel()
        ready = true
        connectedName = peripheral.name ?? "XIAO"
        devices.removeAll()
        discoveredIDs.removeAll()
        status = "已连接，可以发送"
    }
    func send(_ text: String) {
        guard ready, !busy, text.utf8.count <= 512 else { return }
        nextID += 1
        guard let data = try? JSONSerialization.data(withJSONObject: ["id": nextID, "text": text]) else { return }
        var wire = data; wire.append(10)
        guard let peer = peer else { return }
        let size = min(20, peer.maximumWriteValueLength(for: .withResponse))
        guard size > 0 else { fail("无法确定写入长度"); return }
        chunks = stride(from: 0, to: wire.count, by: size).map { wire.subdata(in: $0..<min($0 + size, wire.count)) }
        incoming.removeAll(); pendingID = nextID; busy = true
        log("发送：\(text)")
        timeout(30) { [weak self] in self?.fail("回传超时，本次消息结果未知；请重连后手动重试") }
        writeNext()
    }
    private func writeNext() {
        guard busy, let peer = peer, let rx = rx, !chunks.isEmpty else { return }
        peer.writeValue(chunks.removeFirst(), for: rx, type: .withResponse)
    }
    func peripheral(_ peripheral: CBPeripheral, didWriteValueFor characteristic: CBCharacteristic, error: Error?) {
        guard peer === peripheral, characteristic.uuid == Self.rxID else { return }
        if let error = error { fail("写入失败：\(error.localizedDescription)"); return }
        // One outstanding ATT write; leave time for the board's stream consumer.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.015) { [weak self] in self?.writeNext() }
    }
    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard peer === peripheral, characteristic.uuid == Self.txID else { return }
        guard error == nil, let data = characteristic.value else { fail("读取回传失败"); return }
        incoming.append(data)
        while let newline = incoming.firstIndex(of: 10) {
            let frame = Data(incoming[..<newline]); incoming.removeSubrange(...newline)
            guard frame.count <= 8192,
                  let object = try? JSONSerialization.jsonObject(with: frame) as? [String: Any] else {
                fail("回传格式错误"); return
            }
            guard let id = object["id"] as? Int, id == pendingID else {
                log("忽略不匹配的回传"); continue
            }
            guard let ok = object["ok"] as? Bool else { fail("回传缺少 ok 字段"); return }
            if ok, let result = object["result"] as? String {
                log("回传：\(result)\n接收字节：\(object["bytes"] ?? "?")")
            } else { log("XIAO 错误：\(object["error"] ?? "缺少 result")") }
            deadline?.cancel(); pendingID = nil; busy = false; chunks = []
        }
        if incoming.count > 8192 { fail("回传过长，已断开") }
    }
    func peripheral(_ peripheral: CBPeripheral, didModifyServices invalidatedServices: [CBService]) {
        if invalidatedServices.contains(where: { $0.uuid == Self.serviceID }) { fail("服务已改变，请重新连接") }
    }
}
