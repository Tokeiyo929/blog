---
title: 构建产物只读：配置声明进 profile，写入交给流水线
category: "[代码解析]"
date: 2026-11-26
project: 炮塔大作战
---

炮塔大作战要开抖音的 iOS 高性能模式，官方内测 80 分位 FPS 平均提升 69.01%，开关是产物 game.json 里的一行配置。10-30 的 `8b039525` 一次提交接完：声明进 CI profile、注入挂构建后钩子，游戏代码零改动。

## 一、手改 game.json：字段丢了也不报错

第一版是在构建完的产物里手改 game.json，加上 `"enableIOSHighPerformanceMode": true`，扫码就能在真机上验。当时觉得这样合理——配置就一行，为它去动 CI 像杀鸡用牛刀。

bug 在下一次构建出现。game.json 是 Cocos 构建每次重新生成的产物，手工字段直接被覆盖；叠加官方的静默回落设计（抖音客户端 <31.6.0、基础库 <3.43.0、iOS <14.5 任一不满足就回落普通模式），字段丢了不会报任何错，真机上只有「明明开了怎么还卡」这一种表现。等哪次构建恰好夹在验证和发版之间，回落就悄悄上线了。这条路的结论就一句：产物只读，配置声明进 profile，写入交给注入脚本。

## 二、`8b039525` 一次提交的落点

六个文件改动全在 ci/ 下：metalslug 和 localtest 两份 profile 声明 gameJson 段、bytedance 的 after-build 钩子、game-json-inject 注入脚本、新抽的公共 json.ps1，以及让老的 runtime-config-injection.ps1 改挂公共模块。

profile 里 bytedance 平台段下声明，放多少字段注入多少：

```json
"bytedance": {
  "gameJson": {
    "enableIOSHighPerformanceMode": true
  }
}
```

注入脚本 `ci/platforms/bytedance/tools/game-json-inject/inject.ps1` 的容错分了三级：profile 没有 gameJson 段记 INFO 日志跳过（不是所有平台都要注入），构建产物里找不到 game.json 才抛异常拦发布，结果写进 CI artifacts 回执：

```powershell
$gameJsonPath = Join-Path $buildDir 'game.json'
if (-not (Test-Path -LiteralPath $gameJsonPath -PathType Leaf)) {
  throw "Cocos bytedance output game.json not found: $gameJsonPath"
}
if (-not (Update-JsonFileProperties -Path $gameJsonPath -Properties $gameJson)) {
  throw "Game.json injection failed: $gameJsonPath"
}
$Context.Artifacts.gameJsonInjection = @{
  status = 'SUCCESS'; path = $gameJsonPath; fields = @($gameJson.Keys)
}
```

抽公共模块是因为复用撞了类型：CI 里原本有份私有 `Update-JsonFileProperties`，签名 `[System.Collections.IDictionary]` 只收哈希表，而 profile 是 ConvertFrom-Json 出来的 PSCustomObject，复用得先手工转换。抽到 `ci/common/json.ps1` 后，哈希表和 PSCustomObject 两种入参都收，存在则覆盖、不存在则新增，末尾以 UTF-8 无 BOM 写回——产物不能带隐形字节头。

Android 官方文档把合并清单定为构建时生成的产物，值用 manifestPlaceholders 在 build.gradle 里声明、由 Gradle 在打包阶段注入；Cocos 官方的自定义构建插件也留了 onAfterBuild 钩子，「构建完成之后调用」是文档原话。官方留的入口都在流水线侧，没有手改产物这一条。

## 三、双模式验收和 2.4.11 的两笔遗留

回落逻辑决定了同一个包要同时跑两种模式：vConsole 里蓝色是高性能、绿色是普通，或者查 `GameGlobal.isIOSHighPerformanceMode`。性能数据也不能取巧——IDE 真机调试不支持高性能模式，只能走预览/正式包加 vConsole。

内存是比帧率更硬的红线。高性能模式跑在 WKWebView 上，官方要求运行期均值不超过 800MB、峰值不超过 1.1GB；游戏进程不挂在抖音主进程里，优化盯的是进程名为 WebContent 的那个。录屏 API 会推高这块内存，要开就只开必要场景。

严格模式和 API 差异对我们是零适配：项目没用到摄像头、麦克风和视频，不过那些 API 在高性能模式下调用即抛异常，以后加这类功能得先回来查官方表格。

真正的遗留有两笔。项目还在 Cocos 2.4.11，吃不到官方称 3.8.3+ 才修的 iOS 14–15.3 drawcall 共享问题（受影响机型约占 6.7%），低端 iOS 反馈掉帧时优先排查这一项；iOS 14.x 的 antialias 参数要动引擎 WebGL 上下文，同样先挂账，真出问题再处理。

## 参考

- [Manage your app's manifest file（Android 官方文档）](https://developer.android.com/studio/build/manage-manifests)
- [自定义构建插件（Cocos Creator 3.8 手册）](https://docs.cocos.com/creator/3.8/manual/zh/editor/publish/custom-build-plugin.html)
