---
title: 特效实现：全工程 0 个 ParticleSystem，特效全是 Spine
category: "[代码解析]"
date: 2026-11-18
project: 猫骑士（Unity 小游戏）
---

迁移猫骑士到 Unity 时先钉死一个事实：全工程一个 ParticleSystem 都没有，特效全是 Spine——`Assets/Root/Spine` 下 42 套 SkeletonData，在 UI 坐标系里直接播。

## 一、0 个粒子系统，不是省事，是继承

`rg ParticleSystem` 扫全工程的 .cs/.prefab/.unity，命中数为 0；UIParticle、SortingGroup 同样是 0。这个决定首先是迁移事实逼出来的：Laya 源工程里的特效本来就是 Spine 动画（治疗泉、技能台、开箱全是 .sk 资产），迁移时资产原样进包，Unity 侧没有再引入第二套粒子体系。42 套 SkeletonData 之外，主角一套单独放在 `Assets/Load/Spine`。

把两套特效体系摆在一起，这个选择的收益才看得清：

| 维度 | 粒子系统方案 | 我们（Spine 方案） |
| --- | --- | --- |
| 特效挂接 | 粒子挂在特效 prefab 上，需要 PrefabHolder 之类的加载器 | Spine 资产按 catalog 键加载，组件预置或运行时挂接 |
| 排序 | 粒子与 UI 混排要 UIParticle/SortingGroup 桥接 | Spine 就是 UI 节点，父子关系即层级 |
| 素材管线 | 美术要学 Unity 粒子 | 美术沿用 Spine，角色和特效一套工具 |
| WebGL 包体 | 每个特效 prefab + 材质 + 贴图 | SkeletonData 六件套（json/atlas/材质） |

代价也直说：粒子擅长的连续光效、区域氛围（雨、雾、流光）用 Spine 做会吃力；目前玩法里没有这类需求，等有了再议。

## 二、三种生命周期：预置复用、即播即毁、列表清理

全工程没有特效对象池。三种播放场景走了三种生命周期，各对齐自己的频率：

| 场景 | 方式 | 回收 |
| --- | --- | --- |
| 开箱特效（高频复用） | prefab 预置 `SpineEffectView`，`Play(variant)` | 播完只 `enabled=false`，实例保留 |
| 死亡魂魄（低频一次性） | 从场景模板 `Instantiate` | `IsComplete` 后 `Destroy` |
| 技能光效（可叠加） | 运行时工厂建实例 | 同类型先 `Destroy` 再建，列表清理 |

预置复用的核心是 `Assets/Root/Script/Core/Component/SpineEffectView.cs`，它管四件事：变体切换、动画名校验、完成回调、防串帧：

```csharp
finished = onFinished; int playback = version;
entry = graphic.AnimationState.SetAnimation(0, "animation", loop);
if (loop) return true;
completed = current => {
    if (playback != version || current != entry) return;
    entry.Complete -= completed; entry = null; completed = null;
    graphic.enabled = false;
    var callback = finished; finished = null; callback?.Invoke();
};
entry.Complete += completed;
```

`Stop()` 会把 `version` 加一，迟到的 Complete 回调靠 `playback != version` 丢弃——同一个组件被快速重播时，上一轮的回调不会误触发。播放前还有一道 `FindAnimation("animation")` 校验，缺动画直接告警返回，不会静默黑屏。

开箱是预置复用的典型调用方（`Frames/Shop/ChestOpeningPanelView.cs`）：`effect.Play(chestType - 1, () => { opened = true; ... })`，播完才亮"下一步"按钮——特效完成就是流程门槛。

死亡魂魄走即播即毁（`Frames/Game/MonsterDeathView.cs`）：

```csharp
soul = UnityEngine.Object.Instantiate(soulTemplate, body.parent, false);
soul.name = "MonsterSoul_" + monster.Index; soul.gameObject.SetActive(true);
soul.Initialize(false); soul.AnimationState.SetAnimation(0, "animation", false);
// ...
private void ReleaseSoul()
{
    if (soul == null) return;
    soul.gameObject.SetActive(false); soul.AnimationState?.ClearTracks();
    UnityEngine.Object.Destroy(soul.gameObject); soul = null;
}
```

敢不做池子的前提：销毁的只是 GameObject 实例，SkeletonData 资产由加载器持有、不随实例销毁；同屏魂魄数量是个位数，Instantiate 的成本可忽略。

技能光效是第三种（`Frames/Game/HeroVisual.cs`）：同类型先清场再建新的，避免两个同类光效叠画面：

```csharp
case 7: case 14:
    for (int i = skillEffects.Count - 1; i >= 0; i--)
        if (skillEffects[i].type == feedback.Type) { Destroy(skillEffects[i].rect.gameObject); skillEffects.RemoveAt(i); }
    var rect = MainWorld.Image("SkillTouch_" + feedback.Type, touchSprites[feedback.Type == 7 ? 0 : 1], transform);
    rect.localPosition = new Vector3(actorX + 10, 20, 0); skillEffects.Add((rect, feedback.Type, 0)); break;
```

## 三、挂接与层级：一个 Node 工厂，父子关系即层级

运行时创建的特效统一从 `MainWorld.Node()` 工厂出生（`Frames/Game/MainWorld.cs`）：

```csharp
internal static RectTransform Node(string name, Transform parent, Vector2 position, Vector2 size)
{
    var node = new GameObject(name, typeof(RectTransform)); node.layer = 5; node.transform.SetParent(parent, false);
    var rect = (RectTransform)node.transform; rect.anchorMin = rect.anchorMax = Vector2.zero; rect.pivot = Vector2.zero;
    rect.anchoredPosition = position; rect.sizeDelta = size; return rect;
}
```

挂到谁下面，层级就在谁里面——不碰 `sortingOrder`。全工程只有一处主动改排序：宠物蛋拖拽时 `dragCanvas.sortingOrder = rootCanvas.sortingOrder + 1`（`PetEggView.cs:16`），因为拖拽物要临时越过整个 UI。其余层级全部靠 `SetParent` 和 `SetAsFirstSibling`。

工厂之上包一层 Spine 专用装配（`HeroVisual.SpineEffect`）：

```csharp
private SkeletonGraphic SpineEffect(string name, string key, string animation, bool loop)
{
    var data = packages.Asset<SkeletonDataAsset>(key);
    var node = MainWorld.Node(name, transform, new Vector2(actorX, 10), Vector2.zero);
    var graphic = SkeletonGraphic.AddSkeletonGraphicComponent(node.gameObject, data);
    graphic.material = UnityEngine.UI.Graphic.defaultGraphicMaterial; graphic.raycastTarget = false;
    graphic.MeshGenerator.settings.pmaVertexColors = false;
    graphic.AnimationState.SetAnimation(0, animation, loop); return graphic;
}
```

三个细节是踩出来的：`raycastTarget = false` 让特效不挡点击；`pmaVertexColors = false` 对齐美术导出的贴图预乘设置；挂接偏移（`actorX + 10, 20`、死亡魂魄的 `deathX + 30`）直接写在视图代码里。偏移没有配置化是当前的债——换绑点要改代码，好在频率不高。

## 四、资产进包：catalog 键 + 内嵌/远程双通道

Spine 资产的包内地址是规则化的：`spine/<source>/<field>`，六件套（json、playbackJson、atlasText、material、atlasAsset、dataAsset）各自注册（`PackageBuildMigration.cs`）：

```csharp
var spine = JObject.Parse(File.ReadAllText(SpineImportMigration.InputPath));
foreach (JObject row in spine["rows"].Where(row => (string)row["textureBundle"] != "Load"))
    foreach (var field in new[] { "json", "playbackJson", "atlasText", "material", "atlasAsset", "dataAsset" })
        // Keep native data with its texture owner; Root-to-FrameHome would form a bundle cycle.
        if (row[field] != null) Own((string)row[field], ((string)row["textureBundle"]).ToLowerInvariant(), "spine/" + (string)row["source"] + "/" + field);
```

注释里的"bundle cycle"是真实的坑：Spine 数据跟着贴图所在的包走，否则 Root 包和 FrameHome 包会互相引用成环。加载端 `Assets/Load/Script/PackageLoader.cs` 双通道：内嵌包走 `resources:///CatKnightBundles/` 常量基址；远程包走 `UnityWebRequestAssetBundle` + `CachedAssetBundle("catknight_" + name, hash, crc)`，并显式禁用原生 Caching——小游戏平台的持久缓存需要渠道适配器，不能指望 Unity 默认行为。

## 五、验收与检查单

特效不靠目检收货。`Tools/check-collected-loot.cjs` 里有专门的分包播放用例：`spine-ui`、`spine-world-ui`、`spine-dungeon-ui` 在真实包里跑，证据落在 `Migration/Evidence/collected-loot-case-spine-ui.json` 等文件。素材缺口也照实记录：源导弹爆炸路径 `spine/baoz/baoz.sk` 在原生导入清单和 Assets 里都没有对应资产，`Migration/SPINE_UI_WIRING.md` 写明"不假造图片或换用不相干 Spine"，而不是拿别的东西凑。

上线前核对：

- `rg ParticleSystem` 保持 0 命中；新特效一律走 Spine，不引入第二套体系
- 新 Spine 资产六件套登记进导入清单，键规则 `spine/<source>/<field>`，贴图归属决定所在 bundle
- 动画名统一 `animation`；`SpineEffectView.Play` 的 FindAnimation 校验不允许被绕过
- 快速重播场景（开箱、技能）必须过 `version` 防串帧，不许裸订阅 Complete
- 缺素材登记进 SPINE_UI_WIRING.md 的"未接"清单，宁可空着不接，不拿不相干资产顶
- 改挂接偏移后跑 `check-collected-loot.cjs --case spine-ui`（或对应场景用例）
