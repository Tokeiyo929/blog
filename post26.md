---
title: 层级即结构：建一次分层容器，运行时只进层不抢序
category: "[代码解析]"
date: 2026-11-23
project: 猫骑士（Unity 小游戏）
---

猫骑士从 Laya 迁到 UGUI 后丢了战场层级：掉落糊在怪物身上，塔换层兄弟序乱抖。1ed9382 建起 Unit/Hero/Drop 三层固定容器恢复原版层序，顺手删掉活了十天的 ApplyBagLift 双源偏移。

## 一、迁移时把层级交给了创建顺序

Laya 原版早就有答案：`BattleMap.ts` 建了三个层容器，`unitLayer.zOrder = 4`、`heroLayer = 5`、`dropLayer = 6`，引擎按数字自动重排。UGUI 没有这个数——**绘制顺序就是兄弟节点的顺序**。迁移后的代码把所有战场对象直挂 `map`，谁后创建谁在上：

```text
map
├─ Monster_3 / Monster_4 ...     ← 创建序决定遮挡
├─ Drop_102031                   ← 掉落生成晚，盖住怪物
└─ (伤害飘字也在这里)
```

当时这么写并非没想：创建序在多数场景恰好贴合直觉，乱序只在特定时机暴露。暴露点是三个——掉落生成晚于怪物，糊在怪物身上；塔每换一层销毁重建 `TowerActors` 根节点，兄弟序跟着抖；英雄挂在 page 下不归 map 管，对齐靠 `ApplyBagLift` 手工搬，那是 11-13 两次提交（`5ff415d9`、`9732982c`）打的补丁，地图抬 326、英雄再抬 326，两个数字靠人肉一致。11-23 的 `1ed9382`（23 文件，+150/-55）一次把三件事收干净。

## 二、恢复原版语义：三层兄弟节点

核心动作在 `MainWorld` 的战场装配里，注释把设计意图钉死：

```csharp
map = Node("BattleMap", page.transform.Find("ui"), Vector2.zero, Vector2.zero);
map.SetAsFirstSibling();
map.anchoredPosition = new Vector2(0, 326);
// Laya BattleMap zOrder 4, 5, 6. UGUI draws these siblings in order.
UnitLayer = CreateLayer("UnitLayer");
HeroLayer = CreateLayer("HeroLayer");
DropLayer = CreateLayer("DropLayer");
```

`CreateLayer` 只是把一个全拉伸的空 RectTransform 挂到 map 下，没有渲染组件，唯一能力是**一个不会变的兄弟位置**。之后所有动态对象只能"进层"，不能改变层与层的关系；归层与 Laya 一一对应：

| 战场元素 | 归属层 | Laya zOrder |
| --- | --- | --- |
| 怪物、NPC、食物建筑 | `UnitLayer` | 4 |
| 英雄、出战宠物 | `HeroLayer` | 5 |
| 地面掉落、伤害飘字 | `DropLayer` | 6 |

塔是唯一换批单位的地方：`TowerActors` 根挪进构造函数、挂在 `UnitLayer` 下，换层只清子节点：根和容器复用，兄弟序不再抖，重试同一层也不会多出节点。英雄进了 HeroLayer 后位置语义变了：英雄坐标活在 map 坐标系里，map 抬 326 英雄自动跟上，于是 `ApplyBagLift` 没活可干了，连同 `heroRestY` 两个捕获字段整段删除：

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

地图偏移 326 现在只在 `MainWorld` 装配时出现一次，几何事实只留这一个出处。

## 三、层序写进断言

`GroundLootUiChecks` 新增 `CheckLayerOrder`：三个兄弟索引必须严格递增；`depth >= 0` 要求**真实渲染过一帧**才采深度（首次跑在渲染前采到 -1，之后改成退出 Play 等真实帧再测）；塔换层后断言宠物实例跨层复用。四个用例跑在 Unity 6000.5.3f1 独立 Play 上全部通过；十几个既有 UiChecks 同步把查找路径改成 `UnitLayer/TowerActors/...`，这套层级结构被断言盯死了。遗留照实说：完整讨伐战斗和真机未测。

Laya 引擎把 zOrder 做成一等属性——`Sprite.ts` 的 setter 存下数字，callLater 重排子节点；Unity 官方文档对 2D 渲染的规则同样是显式数值："Unity renders sublayers in numerical order, so lower values render behind higher values"（Order in Layer）。UGUI 的 Canvas 内没有 per-node 数值，还是开头那条兄弟序规则；我们用固定容器把数字语义补回来：层建一次、只进层，每个战场对象等于有一个只读的 zOrder。

这次没发明新机制：UGUI 只认兄弟序，那就把原版语义原样搬进来。三层节点、一个偏移出处、一组硬断言，够稳了。

## 参考

- [LayaAir 引擎（GitHub）](https://github.com/LayaAir/LayaAir)：`Sprite.zOrder` setter 存数字后 callLater 重排子节点
- [Unity 手册：2D renderer sorting](https://docs.unity.com/en-us/engine/current/manual/unity2d/sprite/sort-sprites/2d-renderer-sorting)：Order in Layer 数值定序
