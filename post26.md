---
title: 战场层级：UGUI 没有 zOrder，我们把 Laya 的 4/5/6 原样搬了回来
category: "[代码解析]"
date: 2026-11-23
project: 猫骑士（Unity 小游戏）
---

猫骑士迁移丢了 Laya 的 zOrder 4/5/6 三层战场：掉落盖住怪物、塔换层重排兄弟序。1ed9382 用三层固定兄弟节点恢复原版层序，顺手删掉了活了十天的 ApplyBagLift 双源偏移。

## 一、迁移时，层级靠创建顺序碰运气

Laya 原版的 BattleMap 有固定 zOrder：单位 4、英雄 5、掉落 6——掉落永远飘在最上面，英雄永远压在单位上面。UGUI 没有 zOrder，**绘制顺序就是兄弟节点的顺序**。迁移后的代码把所有战场对象直挂 `map`：怪物、NPC、掉落、飘字、建筑全在同一层，谁后创建谁在上：

```text
map
├─ Monster_3 / Monster_4 ...     ← 创建序决定遮挡
├─ Drop_102031                   ← 掉落生成晚，盖住怪物
├─ TownBuilding8                 ← 早创建，被一切后生者盖住
└─ (伤害飘字也在这里)
```

后果在三个场景爆发：地上的掉落物生成晚于怪物，直接糊在怪物身上；塔每换一层就销毁重建 `TowerActors` 根节点，兄弟序在 map 下抖动；英雄挂在 page 下不归 map 管，与战场的对齐靠 `ApplyBagLift` 手工搬——这套 hack 是 11-13 两次提交（`5ff415d9`、`9732982c`）为"成长坞留在战场"打的补丁，地图抬 326、英雄单独再抬 326，两处数字必须人工保持一致。

11-23 的 `1ed9382`（23 文件，+150/-55）一次把这三件事收干净。

## 二、三层兄弟节点：顺序建一次，永远不变

核心动作在 `Frames/Game/MainWorld.cs` 的战场装配里，代码注释把设计意图钉死：

```csharp
map = Node("BattleMap", page.transform.Find("ui"), Vector2.zero, Vector2.zero);
map.SetAsFirstSibling();
map.anchoredPosition = new Vector2(0, 326);
// ...
// Laya BattleMap zOrder 4, 5, 6. UGUI draws these siblings in order.
UnitLayer = CreateLayer("UnitLayer");
HeroLayer = CreateLayer("HeroLayer");
DropLayer = CreateLayer("DropLayer");
```

`CreateLayer` 只是把一个全拉伸的空 RectTransform 挂到 map 下——没有任何渲染组件，它提供的唯一能力是**一个不会变的兄弟位置**。之后所有动态对象只能"进层"，不能改变层与层的关系。英雄在装配时从 page 下的旧父节点迁进 HeroLayer，`anchoredPosition` 原值保留，宠物跟着英雄同层。

## 三、归层清单：每个对象只有一个去处

| 战场元素 | 归属层 | 对应 Laya zOrder |
| --- | --- | --- |
| 怪物、事件 NPC、食物建筑、城建入口 | `UnitLayer` | 4 |
| 英雄、出战宠物 | `HeroLayer` | 5 |
| 地面掉落、伤害飘字、buff 掉落 | `DropLayer` | 6 |
| 英雄移动烟雾 | map 的第一个子节点 | 垫在三层之下 |

落点改造散在各个 World 里：`DungeonWorld` 的怪物/ NPC/食物建筑从 `world.Map` 改挂 `world.UnitLayer`，`GroundLootView` 和 `BuffDrop` 改挂 `world.DropLayer`；`MainWorld.ShowDamage` 的飘字实例化父节点从 `map` 改为 `DropLayer`——飘字永远在最上层，不再跟怪物抢遮挡。唯一不在三层里的是移动烟雾（`HeroMotionView.cs`）：它是纯背景装饰，`SetAsFirstSibling()` 垫到 map 下所有兄弟之前。

**层的名字、数量、顺序都与 Laya 一一对应**。这不是新设计，是恢复原版语义——迁移保真优先于自创抽象。

## 四、塔换层：复用根，只清子节点

塔是唯一会"换一批单位"的战场。旧实现每层销毁重建 `TowerActors` 根，兄弟序每次抖动；新实现把根的创建挪进构造函数，挂在 `UnitLayer` 下，换层只清子节点（`Frames/Game/TowerWorld.cs`）：

```csharp
public TowerWorld(MainWorld world, MainPage page, ...)
{
    // ...
    root = MainWorld.Node("TowerActors", world.UnitLayer, Vector2.zero, Vector2.zero);
    try { BuildViews(); } catch { Dispose(); throw; }
}
// 换层/重试时：根不动，只清子节点
foreach (Transform child in root)
{
    child.gameObject.SetActive(false);
    UnityEngine.Object.Destroy(child.gameObject);
}
```

这条规则和原版对齐：塔内掉落留在当层的单位容器里（不进 DropLayer），换层随单位一起清掉。重试同一层走同一条路径——根和容器复用，不会因为重来一次而多出一层节点。

## 五、顺手拆掉十天前的 hack

英雄进了 HeroLayer 之后，位置语义变了：英雄坐标现在活在 map 的坐标系里，map 抬 326，英雄自动跟上去。于是 `ApplyBagLift` 的两处手工对齐失去了存在理由，整段删除（`Frames/Game/MainPage.cs`）：

```csharp
// 删除的旧 hack：地图抬一次、英雄再抬一次，两个 326 靠人肉一致
internal void ApplyBagLift()
{
    const float battlefieldOffset = 326;
    if (world.Map != null) world.Map.anchoredPosition = new Vector2(world.Map.anchoredPosition.x, battlefieldOffset);
    var hero = (RectTransform)heroView.transform;
    hero.anchoredPosition = new Vector2(hero.anchoredPosition.x, heroRestY + battlefieldOffset);
}
```

连同 `heroRestY`/`heroRestCaptured` 两个捕获字段一起清掉。地图偏移 326 现在只在 `MainWorld` 装配时出现一次——**一个几何事实只允许一个出处**，这是这次提交比"把层级修好"更值钱的部分。

## 六、层级被断言进世界结构

`Editor/GroundLootUiChecks.cs` 新增 `CheckLayerOrder`，把层序写成硬断言：

```csharp
check(unit.transform.IsChildOf(units) && hero.parent == heroes && pet.transform.parent == heroes &&
    units.GetSiblingIndex() < heroes.GetSiblingIndex() && heroes.GetSiblingIndex() < drops.GetSiblingIndex() &&
    unit.depth >= 0 && pet.depth > unit.depth, context + " keeps rendered pet above units and stable layer order");
check(Vector3.Distance(hero.position, map.TransformPoint(new Vector3(0, 390, 0))) < .01f,
    context + " keeps prefab hero origin on the lifted battlefield");
```

三个要点：兄弟索引必须严格递增；`depth >= 0` 要求**真实渲染过一帧**才采深度（首次跑在渲染前采到 -1，报告保留在 `20261123-091523-275-ground-loot-ui`，之后改成退出 Play 等真实帧再测）；塔换层后断言 `secondPet == towerPet`——宠物实例跨层复用，不是重建。

验证跑在 Unity 6000.5.3f1 独立 Play 上（`rtk proxy unity.exe command script eval --file Library/CliChecks/battlefield-layers/<用例>.cs`，运行目录 `Library/PlayChecks/collected-loot/runs/`）：`ground-loot-ui`（副本掉落归层 + 塔换层/重试 + Canvas 深度，10.1s）、`tower-runtime-ui`（入口到结算回主线，24.5s）、`character-motion-ui` 与 `combat-damage-ui`（移动烟雾与三模式伤害飘字，约 9s/14s）全部通过。十几个既有 UiChecks 同步把查找路径改成 `HeroLayer/BattlePet_0`、`UnitLayer/TowerActors/...`——层级成了被全套房检查的世界结构，不再是隐式约定。

遗留照实说：完整讨伐战斗和真机未测；`refresh-unity.cjs` 因禁用代理返回 `EDITOR_NOT_RUNNING`，编译确认走的静态检查 + Console 人工核对（0 错误）。

## 七、上线前核对

- 战场对象只准挂三层之一：单位进 `UnitLayer`、英雄宠物进 `HeroLayer`、掉落飘字进 `DropLayer`，禁止再直挂 `map`
- 层在装配时创建一次，任何玩法不得销毁或重建层节点；塔换层只清 `TowerActors` 子节点
- 新增战场元素先问 Laya 原版的 zOrder，对不上层的先查原版再归层
- 改动层级相关代码必须过 `ground-loot-ui` 用例；采深度断言前确认已渲染真实帧（`depth >= 0`）
- 战场几何偏移只认 `MainWorld` 的 326，禁止在 page 层再抬任何东西

层级问题的正解不是发明新机制，而是承认 UGUI 的规则（兄弟序即绘制序），然后把原版的语义原样搬进这条规则里——三层节点、一个偏移出处、一组硬断言，就够稳了。
