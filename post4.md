---
title: 存档设计：15 个模块一个事务，冲突时拒绝写入
category: "[代码解析]"
date: 2026-11-18
project: 猫骑士（Unity 小游戏）
---

猫骑士没用 PlayerPrefs 存档：15 个模块打进一个 checkpoint，桌面/网页/微信/抖音四个后端共用一套编解码，检测到外部改动会让保存直接抛异常。

## 一、后端抽象只有两个原语

存档的存储层被压成一个接口 `IAccountStorage`：`Load()` 返回 JObject，`Save(JObject)` 落盘。四个平台各给一个实现，上层完全不感知差异：

| 平台 | 后端 | 落点 |
| --- | --- | --- |
| Windows/编辑器 | `AtomicJsonSave` | `persistentDataPath/local-account.json` |
| web-mobile（网页） | jslib 桥 → `localStorage` | `catknight/web/{projectCode}/{channelCode}` |
| 微信/抖音/快手小游戏 | jslib 桥 → `wx/tt/ks.getStorageSync` | `catknight.account.v1/{scope}` |
| 微信/抖音云存档 | HTTPS 上传/下载 | `catknight-account-v1` 信封 |

桌面端的原子写在 `Core/Sys/AtomicJsonSave.cs`，写之前先把现有文件读一遍——损坏的存档必须以错误形式暴露，而不是被无声覆盖：

```csharp
if (File.Exists(path)) Load();
var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
try
{
    var bytes = new UTF8Encoding(false).GetBytes(text);
    using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
    {
        stream.Write(bytes, 0, bytes.Length);
        stream.Flush(true);
    }
    if (File.Exists(path)) File.Replace(temporary, path, path + ".bak");
    else File.Move(temporary, path);
}
```

小游戏端没有文件系统可依赖，读写走 jslib 桥 `Assets/Plugins/WebGL/ChannelServices.jslib`，按渠道选 SDK：

```js
CatKnight_ChannelRead: function (key) {
  var name = UTF8ToString(key);
  var web = (globalThis.__CHANNEL_CONFIG__ || {}).platform === 'web-mobile';
  var data = web ? globalThis.localStorage.getItem(name) : CatKnightChannel.api().getStorageSync(name);
  if (data === undefined || data === null || !web && data === '') data = null;
  if (data !== null && typeof data !== 'string') throw Error('invalid-storage-type');
  result = {success:true,data:data};  // ...
}
```

`api()` 按 platform 返回 `wx`/`tt`/`ks`，网页则退回 `localStorage`——一套 C# 代码，四端行为一致。

## 二、编解码：15 个模块 + 21 个旁路键

存档不是一个 JSON 对象随便塞。`Core/Sys/AccountStorageCodec.cs` 把数据组织成"固定清单"：15 个核心模块以 `dat_{id}` 为键，模块 id 是写死的长数组，缺一个都算存档损坏：

```csharp
// Fixed source ids. Full module restore implementations are migrated separately.
public static readonly IReadOnlyList<int> ModuleIds = Array.AsReadOnly(new[] {
    1, 2, 3, 4, 1002, 2002, 2001, 1003, 2003, 3001, 1004, 1005, 1006, 1100, 1101
});
```

模块之外还有 **21 个旁路键**（`eqpLcks`、`guideArrs`、`dailyTask`、`onlineT` 这类独立小状态），集合写在同一个文件里，`IsAccountSideKey()` 判定归属。信封是一个 `Rec` 记录加 `datVer` 版本号，版本格式是 `YYMMdd`（`Core/Util/GameClock.cs`）：

```csharp
public string SaveVersion(double milliseconds = 0)
{
    var date = milliseconds == 0 ? RulesLocalDate() : LocalDate(milliseconds);
    // Original getDateString does not pad years below 10 after year % 100.
    return (date.Year % 100).ToString(CultureInfo.InvariantCulture) + date.ToString("MMdd", CultureInfo.InvariantCulture);
}
```

注释里的坑值得抄下来：源工程 `getDateString` 对 2009 年这种 `%100 < 10` 的年份不补零，新实现必须保持同样的不补零行为，否则老存档的版本比对会错位。兼容性藏在注释里，不在文档里。

## 三、保存是一个事务，不是一次写文件

`Core/Sys/AccountPersistence.cs` 的 `TrySave()` 把保存做成事务：先拍快照，再检测外部改动，确认自己上次提交的状态还躺在存储里，才允许覆盖：

```csharp
long capturedRevision = revision;
var snapshot = models.Session.CreateStorageSnapshot(version());
Active();
// Detect an external replacement before overwriting another account/cloud decision.
if (!JToken.DeepEquals(committed, storage.Load())) throw new InvalidOperationException("Account storage changed since restore; retain both states for recovery");
storage.Save(snapshot);
committed = (JObject)snapshot.DeepClone();
if (revision == capturedRevision) pending.Clear();
```

`DeepEquals` 那一行是整个设计的锚点：如果存档在恢复之后被别的进程、别的账号或云同步改过，**保存直接抛异常**，异常消息就是处置方案——"retain both states for recovery"，两份状态都留着，人来裁决。绝不静默覆盖。配合 `saving` 重入保护和 `revision` 对账（保存期间来了新变更就不清 pending），一次保存要么完整落地、要么完整失败。

## 四、云同步：冲突不猜，状态置 Conflict

微信/抖音的云存档走 `ChannelAccountSession`（HTTPS 上传/下载），本地信封由 `ChannelAccountStorage` 管理。信封字段把同步所需的一切都带上：`schema`、`scope`、`records`、`updatedAt`、`remoteTimestamp`、`syncedHash`：

```csharp
private JObject Wrap(JObject records, double updated, double remote, string synced) => new JObject {
    ["schema"] = 1, ["scope"] = Scope, ["records"] = records.DeepClone(), ["updatedAt"] = updated,
    ["remoteTimestamp"] = remote, ["syncedHash"] = synced };
```

本地脏检测用 SHA256：`Hash(records) != syncedHash` 即为脏。上传请求带签名（`MD5(timestamp + version + json + signingKey)`），而冲突判定是三处显式检查——本地有值但远端时间戳非零、远端时间戳对不上、远端记录哈希对不上，任何一处命中就 `Status = "Conflict"` 直接返回：

```csharp
if (local != null && Storage.RemoteTimestamp != 0) { Status = "Conflict"; return; }
// ...
else if (remote.Timestamp != Storage.RemoteTimestamp || !Storage.MatchesBase(remote.Records)) { Status = "Conflict"; return; }
```

冲突不自动合并、不挑一边覆盖——把 Conflict 状态交给上层 UI 呈现，和 `TrySave` 的"抛异常留两份"是同一个哲学：**存档出错时，宁可停住，不可猜错**。

## 五、验证：30,801 条断言 + 向量对照

这套存档的回归不靠手测：`Migration/ACCOUNT_STORAGE.md` 记录 **30,801 条 account 断言**通过、1396 个代码哈希对账（证据 `Migration/Evidence/account-storage-verification.json`）。渠道同步逻辑另有一层"向量检查"：`Tools/account-session-vectors.cjs` 在 vm 里加载 Laya 源工程的 TS 实现，把新旧两端在同样输入下的行为逐例对照——迁移不等于重写，行为要和源实现对表。

上线前核对：

- 新增存档字段先进 15 个模块或 21 个旁路键清单，禁止绕过 codec 直接读写存储
- `SaveVersion` 的不补零行为不许"修好"；改日期逻辑先跑向量对照
- 任何绕过 `AccountPersistence.TrySave` 的写路径都是 bug；云同步冲突只能置 Conflict，不许自动覆盖
- 平台后端改动后，桌面 `.bak` 回滚、网页 localStorage、小游戏 getStorageSync 三条路都要过一遍
- 存档损坏场景写进用例：坏 JSON、缺模块、信封字段缺失必须抛 FormatException，不许静默重建
