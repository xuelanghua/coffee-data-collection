# App 打包与自行测试流程

更新时间: 2026-06-30T06:11:45Z

## 当前边界

- 当前 App 工程目录: `coffee-collector-app/`
- 当前 `npm run build:app` 仅做 UniApp App 骨架构建就绪检查，不产出 APK/IPA。
- 本轮不执行 App 端测试，不声明 App 真机验收 PASS。
- 用户自行打包、自行真机测试，测试反馈回传后再进行修复和调整。

## 打包前准备

1. 确认后端服务地址
   - App API 客户端支持传入 `baseUrl`。
   - 打包前需要确认 App 运行时指向的后端地址，例如局域网地址、准生产域名或公网 HTTPS 地址。
   - 真机访问本机后端时，不要使用 `localhost`，应使用电脑在同一网络下的局域网 IP 或可访问域名。

2. 确认 Android/iOS 权限
   - `manifest.json` 已声明:
     - Camera: 用于现场分类照片和设备采集屏幕拍摄。
     - Location: 用于地块圈选、点位定位和照片水印。

3. 确认 App 页面
   - 登录: `src/pages/login/index`
   - 现场采集: `src/pages/collect/index`
   - 圈选地块: `src/pages/plot-map/index`
   - 拍照水印: `src/pages/photo-capture/index`
   - 上传队列: `src/pages/upload-queue/index`
   - 退回修改: `src/pages/returns/index`

## 方式一: HBuilderX 打包 Android APK

1. 安装 HBuilderX。
2. 打开 HBuilderX，选择“文件 -> 导入 -> 从本地目录导入”。
3. 选择项目目录:

```text
/Users/xuelang/Documents/Code/Coffee Data Collection/coffee-collector-app
```

4. 打开 `manifest.json`，检查:
   - App 名称: `普洱咖啡采集`
   - AppID: `__UNI__PUER_COFFEE`
   - 版本号: `0.1.0`
   - 版本码: `1`
   - 相机和定位权限说明。

5. 配置后端 API 地址。
   - 如当前页面/环境还未提供配置入口，需要在打包前确认运行时 `baseUrl` 注入方式。
   - 推荐先使用可被手机访问的后端地址，例如:

```text
http://电脑局域网IP:8000
```

6. 选择“发行 -> 原生 App-云打包”。
7. 选择 Android。
8. 调试阶段可选择测试证书；正式验收前应使用项目证书。
9. 云打包完成后下载 APK。
10. 安装到 Android 真机。

## 方式二: HBuilderX 运行到 Android 真机

1. Android 手机开启开发者模式。
2. 开启 USB 调试。
3. 用 USB 连接当前电脑，并在手机上允许调试授权。
4. HBuilderX 中选择“运行 -> 运行到手机或模拟器 -> 运行到 Android App 基座”。
5. 在真机上打开 App，按测试清单操作。

## 方式三: iOS 打包

1. 准备 Apple 开发者账号、证书和描述文件。
2. HBuilderX 导入 `coffee-collector-app`。
3. 检查 `manifest.json` 和权限说明。
4. 选择“发行 -> 原生 App-云打包”。
5. 选择 iOS，配置证书和描述文件。
6. 下载 IPA 后通过 TestFlight、Apple Configurator 或企业签名方式安装。

## 自行测试最小闭环

请优先验证以下主流程，并记录截图或录屏:

1. 登录
   - 使用手机号 + 密码登录。
   - 登录成功后进入现场采集页。

2. 现场圈选地块
   - 进入圈选地块页。
   - 在地图上圈选种植地块。
   - 检查面积是否自动计算。

3. 创建采集
   - 创建地块、采集点和采集事件。
   - 确认 Plot_ID、Point_ID、Event_ID 是否生成或显示。

4. 拍照和水印
   - 进入拍照页。
   - 拍摄设备屏幕或现场照片。
   - 检查水印是否包含必要信息。

5. OCR 和校正
   - 调用自开发 OCR。
   - 检查识别结果是否填入对应输入框。
   - 手动校正字段。

6. 上传队列
   - 弱网或断网后保存草稿。
   - 恢复网络后观察上传队列。

7. 提交和 Web 审核
   - App 提交采集事件。
   - Web 后台查看同一条详情，检查地块、图片、OCR 信息是否在同一详情页展示。

## 反馈格式

请尽量按以下格式回传:

```text
设备型号:
系统版本:
App 安装方式:
后端地址:
测试账号:
网络环境:

通过的步骤:
失败的步骤:
失败截图/录屏:
错误提示:
大概发生时间:
是否可复现:
补充说明:
```

## 当前 BLOCKED 记录

- App 真机验收: 等待用户自行打包和真机测试反馈。
- 真实设备照片样本: 用户确认暂不提供，后续补充测试。
- 准生产环境: 尚未提供。
- 华为 OCR: 用户确认暂不配置，继续使用自开发 OCR 插件。

