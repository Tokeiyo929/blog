---
title: 血条的策略由数量决定：批量走池化轮询，唯一走事件驱动
category: "[代码解析]"
date: 2026-11-06
project: 炮塔大作战
---

炮塔大作战的血条踩过完整的坑路：boss 多层血条六天就废弃、表现字段污染了逻辑快照，最终收敛成三条：小兵池化轮询，boss 事件驱动加 100 管假分段，战车补缓冲。

## 一、多层血条六天就死了：表现概念混进了逻辑快照

10-15 的 `1efc00be`（「子母弹子弹，boss多层血条」）是当时的直觉做法：美术要多管血、颜色渐变，那就真建多根血条，配置里加阶段，快照里加字段：`EntitySnapshot.phase`（"当前血条/形态阶段，0-based"），prefab 上配「阶段节点」数组。当时觉得配置驱动最省事。

十天后的死亡回收重构（10-21 `08271c98`）把它整个废弃了：血条分几段是纯表现层的决定，逻辑快照却被迫携带 `phase`，每份快照复制、每个消费方都跟着这个字段走。换一次血条设计，改的是逻辑层。diff 里 `phase` 字段、赋值、阶段节点 property 连成一串删掉，boss 血条从此只靠快照里的 `hp/maxHp` 两个数字活着。教训就一条：**快照里只准有逻辑事实**，分段几根、什么颜色全是画的事，别让它进数据结构。

## 二、数量决定策略：小兵池化轮询，boss 事件驱动

小兵同屏几十个，更新方式是**集中轮询**：渲染层不持有血量逻辑，唯一数据源是逻辑层下发的 `EntitySnapshot`，`HpBarManager` 持池、按 `entityId` 对账，怪死了回池不销毁。每帧对账用自增版本号兜底，不维护"上帧的怪列表"再做差集：

```typescript
public syncExistingBars(entities: EntitySnapshot[], resolveEntityView: HpBarViewResolver): void {
    if (this.barCount <= 0) return;
    this.existingEntityVersion++;
    for (let i = 0; i < entities.length; i++) {
        // 给 existingEntityVersions[entity.id] 打当前版本号，血量非法则 remove
    }
    this.removeMissingBars();   // 版本号落后的血条 = 怪已消失，回池
}
```

位置同步不把血条挂到怪节点上：每帧把怪头顶锚点的世界坐标转进统一 UI 层，怪节点销毁、层级抖动都碰不到血条。boss 是屏幕顶部的唯一 UI，走**事件驱动**：`CombatEventBridge` 比对上次已播报的 `hp/maxHp`，没变化就不发事件，一帧最多一条，UI 层挂个监听就完事。

美术给 boss 的图是"多管血"样式，这次没真建 100 根管，除法加取模就把分段 fake 出来了：

```typescript
public showHp(hp: number, maxHp: number): boolean {
    const hpPerBar = maxHp / BOSS_HEALTH_BAR_COUNT;   // 总血量均分 100 根管
    const activeBarIndex = Math.min(BOSS_HEALTH_BAR_COUNT - 1,
        Math.max(0, Math.floor((maxHp - hp) / hpPerBar)));   // 打空了几根管
    // ...当前管内剩余血量的比例
    this.progressBar.progress = activeBarRatio;
    this.setFillImage(this.progressBar, activeBarIndex);     // 按管序号取模换色
}
```

一个 ProgressBar 只显示当前管，后面垫一个副本当"下一管"预览，换色不跳帧；`showHp` 只有从隐藏到显示那一次返回 `true`，UI 层拿它触发 boss 登场警告。10-22 的孵化兽重构（`4cf565d5`「preserve segmented boss health」）动过血条周边一圈，这套假分段原样活了下来，比节点方案扛重构。

## 三、缓冲终落地：给战车，不给小兵

参考的教程（[BV15J411x7do](https://www.bilibili.com/video/BV15J411x7do/)，源码在 [zheyuanzhou/Youtube-Unity-Tutorial EP45](https://github.com/zheyuanzhou/Youtube-Unity-Tutorial/tree/master/EP45_Health%20Bar)）招牌是受伤缓冲：底层黄条慢追上层红条，打击感的核心。我们 10 月没给小兵做缓冲，掉血瞬间落底。11-05 的 `0501f46a`（「血量缓冲」）把它补在了**战车血条**上：缓冲条由 `GameFrame` 集中持有驱动，不引入第二个每帧组件：

```typescript
if (!visible || !wasVisible || progress > previousProgress) {
    cc.Tween.stopAllByTarget(this.carHpBufferBar);
    this.carHpBufferBar.progress = progress;        // 回血/首显/隐藏：直接对齐，只降不升
} else if (progress < previousProgress) {
    cc.Tween.stopAllByTarget(this.carHpBufferBar);
    cc.tween(this.carHpBufferBar).delay(0.3).to(0.5, { progress }).start();   // 掉血：慢追
}
```

`onDisable` 停掉 tween 并对齐，缓冲状态不跨局残留；`tools/tests/car-hp-buffer.test.cjs`（117 行）把只降不升、回血对齐、隐藏清理全部钉死。战车是玩家唯一盯着的一条血，缓冲的打击感收益全落在它身上；小兵几十条，瞬间落底反而干脆。

两条主流做法都对得上。教程的双层 Image 缓冲是社区通用做法，我们原样借了"只降不升"这条规则；池化是官方标准，Cocos Creator 文档原话："假如玩家在一关中要杀死 100 个敌人，但同时出现的敌人不超过 5 个，那我们就只需要生成 5 个节点大小的对象池，然后循环使用就可以了”，对账这一环则换成了自增版本号。血条小到没人把它当架构问题，但多层血条那六天证明它值得复盘：这次没发明新东西，双层缓冲、对象池都是现成答案，我们做的只是让每条策略跟着数量走。

## 参考

- [【中文字幕】Unity血条UI设计和受伤缓冲效果（B站）](https://www.bilibili.com/video/BV15J411x7do/)
- [zheyuanzhou/Youtube-Unity-Tutorial EP45_Health Bar（GitHub）](https://github.com/zheyuanzhou/Youtube-Unity-Tutorial/tree/master/EP45_Health%20Bar)
- [Cocos Creator 2.x 手册：对象池](https://docs.cocos.com/creator/2.4/manual/zh/scripting/pooling.html)
