---
title: 血条实现解析：从Unity经典教程到炮塔大作战
category: "[代码解析]"
date: 2026-11-06
project: 炮塔大作战
---

## 一、从一篇经典教程说起

血条大概是游戏 UI 里最"人人都会做"的组件，但真到批量怪 + Boss 同屏的场景，做法差异会直接反映在帧率上。最近复习了 B 站的一篇经典教程【中文字幕】Unity血条UI设计和受伤缓冲效果（[BV15J411x7do](https://www.bilibili.com/video/BV15J411x7do/)，配套源码在 [zheyuanzhou/Youtube-Unity-Tutorial 的 EP45_Health Bar](https://github.com/zheyuanzhou/Youtube-Unity-Tutorial/tree/master/EP45_Health%20Bar)），然后对照我们项目（Cocos Creator）里血条的实际实现，把三种做法整理成一篇记录。

教程的做法是经典的**双层 Image**：底层一条黄色缓冲条，上层一条红色即时条，怪掉血时红条立刻落下去，黄条在后面慢慢追——这个"受伤缓冲"就是血条打击感的核心来源。源码 `HealthBar.cs`：

```csharp
public class HealthBar : MonoBehaviour
{
    public Image hpImage;          // 红色即时条
    public Image hpEffectImage;    // 黄色缓冲条

    [HideInInspector] public float hp;
    [SerializeField] private float maxHp;
    [SerializeField] private float hurtSpeed = 0.005f;

    private void Update()
    {
        hpImage.fillAmount = hp / maxHp;

        if (hpEffectImage.fillAmount > hpImage.fillAmount)
        {
            hpEffectImage.fillAmount -= hurtSpeed;   // 缓冲条每帧线性回落
        }
        else
        {
            hpEffectImage.fillAmount = hpImage.fillAmount;
        }
    }
}
```

两个细节值得注意：

- **缓冲只降不升**：回血时红条超过黄条，黄条直接对齐（`else` 分支），不会出现"回血却先看到黄条往上顶"的怪相。
- **每个怪挂一个脚本、每帧跑一次 Update**。教程场景里就几个怪，没问题；但同屏几十上百个怪时，这就是 N 个独立 Update + N 次 fillAmount 赋值，其中大部分帧血量根本没变。

## 二、我们的小兵血条：池化 + 快照轮询

我们项目是 Cocos Creator，血条这块走了另一条路：**渲染层不持有血量逻辑**，血量的唯一数据源是逻辑层下发的 `EntitySnapshot`（含 `hp`、`maxHp`、`isBoss`），渲染层每帧拿快照做同步。

单条血条本身极薄，`HpBar.ts` 全部逻辑就一件事——夹值、赋 progress：

```typescript
public setHp(hp: number, maxHp: number): void {
    const ratio = Math.max(0, Math.min(hp / maxHp, 1));
    this.node.active = true;
    this.progressBar.progress = ratio;
}
```

真正干活的是 `HpBarManager`。它维护一个 `entityId -> HpBar` 的表，血条预制体走对象池复用，怪死了不销毁、回池子：

```typescript
public showOrUpdate(entity: EntitySnapshot, entityView: HpBarAnchorView): void {
    if (!entity || !entityView || entity.hp <= 0 || entity.maxHp <= 0) return;
    if (entity.isBoss === true) {
        this.remove(entity.id);   // Boss 不走小兵血条，交给 BossHpBar
        return;
    }
    let bar = this.bars[entity.id];
    if (!bar) bar = this.createBar(entity.id);
    this.updateBar(bar, entity, entityView);
}
```

每帧的全量对账在 `syncExistingBars` 里，用一个自增版本号解决了"哪些怪还活着"的判断——遍历快照时给见到的怪打上当前版本号，遍历完把没打上版本号的血条全部回收：

```typescript
public syncExistingBars(entities: EntitySnapshot[], resolveEntityView: HpBarViewResolver): void {
    if (this.barCount <= 0) return;
    this.existingEntityVersion++;
    for (let i = 0; i < entities.length; i++) {
        const entity = entities[i];
        // ...给 existingEntityVersions[entity.id] 打当前版本号，血量非法则 remove
    }
    this.removeMissingBars();   // 版本号落后的血条 = 怪已消失，回池
}
```

这比维护一份"上帧的怪列表"再做差集要稳：不需要处理漏删，版本号天然兜底。位置同步也没用血条挂 entity 子节点的方式，而是每帧把 entity 头顶锚点的世界坐标转成血条父节点下的局部坐标——血条统一挂在同一个 UI 层，不受怪节点销毁、层级抖动影响：

```typescript
private updateBar(bar: HpBar, entity: EntitySnapshot, entityView: HpBarAnchorView): void {
    if (!bar || !entityView || !entityView.node || !cc.isValid(entityView.node)) return;
    entityView.getHpBarWorldPosition(entity, this.tempWorldPosition);
    parent.convertToNodeSpaceAR(this.tempWorldPosition, this.tempLocalPosition);
    bar.setLocalPosition(this.tempLocalPosition);
    bar.setHp(entity.hp, entity.maxHp);
}
```

跟教程对比一下：教程是"每个怪自治"，我们是"一个管理者每帧集中同步"。后者的好处是怪的数量和逻辑复杂度解耦——怪再多的也只是快照数组变长，血条系统本身的每帧成本不变；而且对象池复用避免了同屏反复 instantiate/destroy 血条节点。

## 三、Boss 血条：事件驱动 + 100 根分段管

Boss 没有走上面那套轮询。小兵血条跟着怪走，Boss 血条是屏幕顶部的固定 UI，走**事件驱动**：逻辑层快照经过 `CombatEventBridge`，比对上次已播报的值，没变化就不发事件：

```typescript
private emitBossHpShow(boss: EntitySnapshot): void {
    if (this.bossVisible && this.lastBossEntityId === boss.id
        && this.lastBossHp === boss.hp && this.lastBossMaxHp === boss.maxHp) return;
    this.bossVisible = true;
    // 记录 lastBoss* 后 emit CoreEvent.CombatBossHpChanged
}
```

小兵走轮询、Boss 走事件，不是风格问题而是数量问题：同屏小兵几十个，轮询+池化最省；Boss 只有一个，事件天然去重后一帧最多一条，UI 层挂个监听就够了。

Boss 血条本身的实现比较有意思。美术给的图是"多管血"的样式（打完一管换下一管、颜色渐变），我们不想真的建 100 个节点，做法是**用数学fake出分段**：把总血量均分成 100 根管，算出当前在第几根管、这根管里占多少，`BossHpBar.ts`：

```typescript
const BOSS_HEALTH_BAR_COUNT = 100;

public showHp(hp: number, maxHp: number): boolean {
    const totalBarCount = BOSS_HEALTH_BAR_COUNT;
    const hpPerBar = maxHp / totalBarCount;
    // 当前是第几根管（已打掉的管数）
    const activeBarIndex = Math.min(totalBarCount - 1,
        Math.max(0, Math.floor((maxHp - hp) / hpPerBar)));
    // 当前管内剩余血量的比例
    const activeBarHp = hp - (totalBarCount - activeBarIndex - 1) * hpPerBar;
    const activeBarRatio = Math.min(1, Math.max(0, activeBarHp / hpPerBar));

    this.progressBar.progress = activeBarRatio;
    this.setFillImage(this.progressBar, activeBarIndex);   // 按管序号换色
    // ...
}
```

一个 ProgressBar 只能显示当前管，所以又实例化了一个副本垫在后面当"下一管"预览——当前管打空时视觉上已经能看到后面那根，衔接不掉帧地换色。换色靠 `ImageLoader` 多图选择器按管序号取模轮播：

```typescript
private setFillImage(progressBar: cc.ProgressBar, barIndex: number): void {
    const imageLoader = progressBar.barSprite.node.getComponent(ImageLoader);
    if (!imageLoader || imageLoader.getCount() === 0) return;
    imageLoader.select(barIndex % imageLoader.getCount());
}
```

外加一个 `x N` 的 Label 显示剩余管数，管数只剩 1 根时自动隐藏。`showHp` 还有个返回值：只有从隐藏到显示的那一次返回 `true`，UI 层拿它触发 Boss 登场的警告演出，血量变化的普通帧不会重复播。

## 四、三种做法对比

| | 教程（Unity EP45） | 小兵血条 | Boss 血条 |
| --- | --- | --- | --- |
| 更新方式 | 每个怪自带 Update | 快照轮询，集中同步 | 事件驱动，带去重 |
| 复用方式 | 不复用，每怪一个组件 | 对象池，按 entityId 复用 | 单例 UI，无池 |
| 受伤缓冲 | 双 Image 慢速追赶 | 无（可加，见下） | 分段管+换色即视觉缓冲 |
| 适用场景 | 怪少、原型快 | 批量同屏单位 | 唯一重要目标 |

三套做法其实是一条演进线：怪少时教程那种自治脚本最省事；怪一多就得收权到 Manager 集中同步 + 池化；目标是唯一焦点时再切回事件驱动，还能顺便做演出钩子。

## 五、把受伤缓冲补回来

教程最大的亮点"受伤缓冲"，我们的小兵血条目前没有——掉血是瞬间落到底的。要补的话不需要回到"每怪一个脚本"的老路，在 `HpBar` 里加一条缓冲 Image，渲染层每帧追一次即可：

```typescript
// HpBar.ts 思路：setHp 只记录目标值，缓冲条由 Manager 每帧统一驱动
public setHp(hp: number, maxHp: number): void {
    this.targetRatio = Math.max(0, Math.min(hp / maxHp, 1));
    this.progressBar.progress = this.targetRatio;   // 即时条立刻动
}

// Manager 的 updateBar 里：
const effect = bar.effectRatio ?? ratio;
bar.effectRatio = Math.max(ratio, effect - HURT_SPEED);   // 只降不升，同教程
bar.effectBar.progress = bar.effectRatio;
```

缓冲条数据存在 `HpBar` 实例上，随对象池一起回收复用，Manager 依然每帧集中驱动，不引入 N 个独立 Update。唯一要注意的是池子复用时把 `effectRatio` 清零，不然上个怪的红条状态会"闪现"到下个怪头上。

## 六、小结

- 受伤缓冲的本质是**两条进度条的速度差**，实现只要几行，打击感提升立竿见影。
- 批量单位血条的核心不是进度条而是**生命周期管理**：池化 + 版本号对账，怪多怪少每帧成本恒定。
- 分段血条不需要 N 个节点，除法 + 取模就能 fake，剩下的交给美术换色。
- 轮询和事件没有高下之分：**数量多的走轮询，数量少的走事件**，Boss 那条事件链顺带解决了警告演出的触发时机。

教程仓库（Unity/C#）和我们的实现（Cocos Creator/TS）引擎不同，但分层思路完全同构——血量数据、血条表现、更新策略三者分开，换引擎换的只是 API。
