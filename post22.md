## 一、高性能模式是什么

我们的小游戏在 iOS 上的帧率一直比安卓差一截。抖音官方给了一个针对性的解法：**iOS 高性能模式**——基于系统 WKWebView 能力的运行时，JS 运行效率大幅提升，游戏只需简单适配即可明显提速。官方内测数据：80 分位 FPS 平均提升 69.01%（32.53 → 54.98）。CPU 压力大的游戏收益更大；Unity 小游戏已默认全量开启，Cocos 这类引擎需要自己接。

本文把官方文档的要点和我们项目实际接入的过程整理成一篇记录。我们的接入改动只有一次提交，全部落在 CI 脚本里，游戏代码零改动。

## 二、开启方式与回落逻辑

配置只有一行，在 `game.json` 里：

```json
{
  "enableIOSHighPerformanceMode": true
}
```

有三道版本门槛，任一不满足都会**静默回落**普通模式：

- 抖音客户端 ≥ 31.6.0
- 客户端基础库 ≥ 3.43.0
- iOS ≥ 14.5（官方 2024 年 10 月数据，覆盖约 96.7% 机型）

回落意味着同一个包要同时跑在两种模式上，上线前两种都得测过。

怎么确认当前跑在哪种模式：真机 vConsole 里看 `GameGlobal.isIOSHighPerformanceMode`，高性能模式下为 `true`，普通模式下是 `undefined`；或者直接看 vConsole 的颜色——普通模式绿色，高性能模式蓝色。

另外局域网预览不支持高性能模式，预览时不要勾选「开启局域网快速预览」。

## 三、我们的接法：CI 注入，不手改 game.json

官方接入看起来就是改一行配置，但 Cocos 项目有个绕不开的坑：**`game.json` 是每次构建的产物**，Cocos 构建时会重新生成它，手工改上的字段下次构建就丢了。

我们的方案是在自建 CI 的构建后（after-build）阶段把字段注入进产物。开关声明在各平台的 profile 里，构建脚本只负责照着 profile 写产物。`ci/profiles/metalslug/profile.json`（localtest 同样处理）：

```json
"gameJson": {
  "enableIOSHighPerformanceMode": true
}
```

`gameJson` 和 `manifest` 平级，放多少个字段就注入多少个，不限于这一个开关。bytedance 平台的 after-build 步骤列表里挂了注入脚本 `ci/platforms/bytedance/tools/game-json-inject/inject.ps1`（节选）：

```powershell
$gameJsonPath = Join-Path $buildDir 'game.json'
if (-not (Test-Path -LiteralPath $gameJsonPath -PathType Leaf)) {
  throw "Cocos bytedance output game.json not found: $gameJsonPath"
}

if (-not (Update-JsonFileProperties -Path $gameJsonPath -Properties $gameJson)) {
  throw "Game.json injection failed: $gameJsonPath"
}

$Context.Artifacts.gameJsonInjection = @{
  status = 'SUCCESS'
  path = $gameJsonPath
  fields = @($gameJson.Keys)
}
```

注意这里的容错分级：profile 里没有 `gameJson` 段就跳过注入（不报错），构建产物里找不到 `game.json` 才抛异常拦截发布。注入结果记进 CI artifacts，方便流水线日志里核对。

字段写入用的是新抽的公共函数 `ci/common/json.ps1`：

```powershell
function Update-JsonFileProperties {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)]$Properties
  )

  $json = Get-Content -Raw -LiteralPath $Path -Encoding UTF8 | ConvertFrom-Json
  foreach ($property in Get-CiJsonProperties -Properties $Properties) {
    if ($json.PSObject.Properties[$property.Name]) {
      $json.($property.Name) = $property.Value
    }
    else {
      $json | Add-Member -NotePropertyName $property.Name -NotePropertyValue $property.Value
    }
  }

  $jsonText = $json | ConvertTo-Json -Depth 80
  [System.IO.File]::WriteAllText($Path, $jsonText, [System.Text.UTF8Encoding]::new($false))
}
```

存在则覆盖、不存在则新增，最后以 UTF-8 无 BOM 写回。这个函数原本是 `runtime-config-injection.ps1` 里的私有实现（只接受哈希表），这次抽成了公共模块，哈希表和 PSCustomObject 两种入参都支持——之后再有"往产物配置里塞字段"的需求都走这一条路。

## 四、内存红线：比帧率更容易翻车的地方

高性能模式跑在 WKWebView 上，内存占用比普通模式高，官方给了明确的红线：

- 运行过程中平均内存不超过 **800MB**，峰值不超过 **1.1GB**；超限可能异常退出、白屏，直接变成用户投诉。
- 游戏跑在**非抖音进程**里，优化时要盯的是小游戏进程（进程名一般为 **WebContent**），别对着抖音主进程优化半天。
- 多 WebContent 进程的识别方法：关掉其他后台应用，看 CPU 占用和 FPS——游戏进程的 CPU 一般不会是 0。
- 录屏（`getGameRecorderManager`）会推高内存，iOS 15.4 以下还会拖累 FPS。确认业务必要性后再接，不要全程录制。

## 五、适配清单

按官方文档过一遍，标注与我们项目的相关性：

**严格模式**：高性能模式要求 JS 严格模式。引擎产物一般自动满足，业务代码要自查一遍。

**API 差异**（不支持的 API 调用即抛异常）：

| API | 表现 |
| --- | --- |
| request / pause / resumeMicrophone | 不支持，抛异常 |
| createCamera | 不支持，抛异常 |
| createFaceDetector / createHandDetector | 不支持，抛异常 |
| video.paintTo / video.play | 仅支持绘制到 2d context 的 canvas，WebGL canvas 无效，视频需改用引擎或 WebGL 纹理绘制 |

我们没有用到摄像头、麦克风和视频，这一块零适配。但"调用即抛异常"意味着以后加这类功能时得先回来查这张表。

**iOS 14.x 帧率问题**：可能出现单帧耗时长但帧率仍低的现象。官方解法是创建 WebGL 上下文时加 `antialias: true`：

```javascript
const canvas = tt.createCanvas();
canvas.getContext('webgl', { antialias: true });
```

Cocos 项目的 WebGL 上下文由引擎创建，这个参数要动引擎层。先记录备查，14.x 真出问题再回来处理。

**iOS 15.3 及以下 drawcall 问题**：多个 drawcall 共享同一份 vertexBuffer/indexBuffer 导致性能问题，受影响机型（iOS 14–15.3）约占 6.7%。官方称 Cocos **3.8.3+** 已针对性修复——我们项目还在 **2.4.11**，享受不到这条修复，如果低端 iOS 设备反馈掉帧，优先排查这一项。

**真机调试不支持**：IDE 的「真机调试」暂不支持高性能模式，调试时不要开这个配置，调试会话里的性能数据也不能作为运行时参考。性能验证只能走预览/正式包加 vConsole。

## 六、上线前检查单

- CI 日志里有 `gameJsonInjection` 成功记录，字段确实进了产物 `game.json`
- 双模式都跑通：vConsole 蓝色是高性能，绿色是普通
- 内存达标：均值 ≤ 800MB，峰值 ≤ 1.1GB（盯 WebContent 进程）
- 录屏要么不开，要么只在必要场景开
- 严格模式自查通过
- 没有用到第五节表格里不支持的 API
- 待观察项：iOS 14.x 的 antialias 问题、iOS 15.3 以下的 drawcall 问题，出问题回到第五节对照处理
