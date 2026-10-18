# XIAOText iOS

用 Xcode 打开本目录的 `XIAOText.xcodeproj`，选择共享 Scheme `XIAOText` 和真实 iPhone。首次安装在 Target → Signing & Capabilities 选择自己的 Team。

## 目录

```text
XIAOText.xcodeproj/          Xcode 工程、内置 workspace、共享 Scheme
XIAOText/
  App/XIAOTextApp.swift      App 入口
  Views/ContentView.swift    SwiftUI 页面
  Services/BLEManager.swift  CoreBluetooth 连接与收发
  Resources/
    Info.plist              App 元数据、蓝牙权限、启动与方向配置
    Assets.xcassets/         AppIcon 图标资源
  Configuration/
    Common.xcconfig         通用构建设置
    Debug.xcconfig          调试设置
    Release.xcconfig        发布设置
```

最低 iOS 16。无需 CocoaPods 或第三方 Swift 包；不需要另建顶层 workspace。Info.plist 由工程读取，不加入 Copy Bundle Resources。图标从 AppIcon 资源编译并由 Xcode 写入最终 Info.plist。

版本为 1.0.1 (2)。Debug Run 使用 LLDB；Profile/Archive 使用 Release。配置包含完整各尺寸图标，使用先前生成的飞行汽车图片。

源码结构调整没有改变 BLE 协议、扫描行为或 XIAO 程序。真实设备安装与图标显示需要在手机上验收，编译成功不代表已验证手机界面。
