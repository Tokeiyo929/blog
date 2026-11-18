---
title: 特效实现：逻辑层不播粒子，四类特效四种回收
category: "[代码解析]"
date: 2026-11-18
project: 炮塔大作战
---

炮塔大作战的逻辑层从不直接播粒子：命中、燃烧、拖尾、碎片四类特效各走各的 Manager 和池，Logic 只往命令缓冲里写一行 RenderCommand。

## 一、边界先画死：Logic 不碰节点

这条边界写在文档里也是代码里——`Docs/CombatWorld说明.md` 的原话是"不直接播放动画、音效或粒子"。逻辑层的输出只有数据：`CombatOutput.pushPlayHitEffect(...)` 这类方法把请求写进 `RenderCommand[]`，`CombatStageView.handleCommand` 在渲染帧统一消费。`RenderCommand` 的注释写明了它的定位：

```text
RenderCommand[]：表现命令，告诉渲染层播放攻击动画、生成子弹、移动子弹、播放命中特效、飘字和音效。
```

边界的好处立刻能兑现：`Render/Null/NullCombatStageView.ts` 实现同一个 `ICombatStageView` 接口，但什么都不渲染，只把快照和命令克隆进数组——无 Cocos 环境下验证整条 Logic 链路时，特效请求是否发出、发了几次，都变成可断言的数据：

```ts
export default class NullCombatStageView implements ICombatStageView {
    public snapshots: CombatSnapshot[] = [];
    public events: CombatEvent[] = [];
    public commands: RenderCommand[] = [];

    public handleCommand(command: RenderCommand): void {
        this.commands.push(this.cloneCommand(command));
    }
    // ...
}
```

## 二、四类特效，四种生命周期

渲染层内部没有"统一特效系统"，而是按生命周期拆成四个 Manager，各配各的回收策略：

| 类别 | Manager | 播放方式 | 回收时机 |
| --- | --- | --- | --- |
| 世界坐标一次性（命中/爆炸/死亡） | `EffectManager` | 动画播完回调 | onComplete → clear → 入池 |
| 实体持续型（燃烧等） | `EntityEffectManager` | 挂到 EntityView 子节点 | `tween.delay(duration)` 到期，重复请求只续期 |
| 子弹拖尾（真粒子） | `BulletViewManager` | `cc.ParticleSystem` | `stopSystem()` 后等残粒消散 |
| 碎片飞溅（伪粒子） | `SplashParticleManager` | sprite 物理模拟 | 池上限 160，超限回收最旧 |

世界坐标一次性特效的映射表和回收链（`Render/Core/EffectManager.ts`）：

```ts
const EFFECT_ASSET_NAMES: { [key: string]: string } = {
    [EffectType.HitBasic]: "HitEffect_01",
    [EffectType.DeathBasic]: "HitEffect_03",
    [EffectType.ExplosionBasic]: "HitEffect_03",
};
// ...
private recycle(view: EffectView): void {
    for (let i = this.activeEffects.length - 1; i >= 0; i--) {
        if (this.activeEffects[i] === view) { this.activeEffects.splice(i, 1); break; }
    }
    const viewType = EFFECT_VIEW_TYPE_PREFIX + view.effectType;
    view.clear();
    this.getPool().put(viewType, view.node);
}
```

`Prefab/Game/Effect/` 下就 9 个 `HitEffect_0X.prefab`，三种逻辑事件复用两个 prefab——特效的种类远少于事件的种类，靠映射表而不是给每种伤害做一个特效。

实体持续型是去重续期设计（`Render/Core/EntityEffectManager.ts`）：同一个实体挂同一个特效，重复命令不重建实例，只重设位置并重置回收定时：

```ts
const key = command.entityId + "_" + command.effectKey;
const existing = this.activeEffects[key];
if (existing) {
    if (existing.node && cc.isValid(existing.node)) existing.node.setPosition(view.getEntityEffectLocalPosition(command.effectKey));
    if (existing.tween) existing.tween.stop();
    existing.tween = this.scheduleRecycle(key, command.duration);
    return;
}
```

挂接偏移由 `EntityView.getEntityEffectLocalPosition()` 提供（默认 y = height * 0.5，特殊特效挂专用 anchor 子节点）——渲染细节归渲染层，Logic 只报"谁、什么特效、多久"。

子弹拖尾是真正的 Cocos 粒子，回收时机最讲究（`Render/Core/BulletViewManager.ts`）：停止发射后残粒还在飞，立刻回收会凭空消失，所以等 `life + lifeVar` 秒：

```ts
private bulletTrailPool: cc.NodePool = new cc.NodePool();
// ...
private stopBulletTrail(bulletId: number): void {
    const particle = this.bulletTrailViews[bulletId];
    if (!particle) return;
    particle.stopSystem();
    this.bulletTrailStopDelays[bulletId] = particle.life + particle.lifeVar;
}
```

碎片飞溅干脆不用粒子系统：`SplashParticleManager` 自己做 sprite 物理模拟（重力、弹跳、摩擦），节点走自管数组池，`maxActiveCount = 160`，超限回收最旧的一颗——碎片数量失控时先保证帧率。

## 三、ViewPool：一个池子，键即约定

四个 Manager 共用 `Render/Core/ViewPool.ts` 这个通用节点池，结构简单到只有两根手指：`pool[viewType]: any[]` 是 LIFO 栈，`get` 先弹栈、空了才 `instantiate`，`put` 只做 deactivate + removeFromParent：

```ts
private pool: { [key: string]: any[] } = {};

public get(viewType: string, prefab: any, parent: any): any {
    const list = this.pool[viewType] || [];
    let node = list.length > 0 ? list.pop() : null;
    if (!node && prefab) node = cc.instantiate(prefab);
    if (node) {
        node.parent = parent;
        if (parent && parent.group) CocosUtil.setGroup(node, parent.group);
        node.active = true;
    }
    return node;
}
```

池没有上限——上限的职责在每个 Manager 手里（碎片 160、实体特效靠 duration 到期）。复用键是字符串约定：`"Effect_" + prefabPath`、`"EntityEffect_" + effectKey`、`prefabPath + "#FlameStream"`，键相同即节点结构相同，跨 Manager 不会串。`EffectView.resolveAnimation()` 还做了资产适配：prefab 里的动画组件是 BaseAnimation、Spine 或逐帧动画，取出来统一当动画播，回收时 `clear()` 复位。

## 四、粒子要跟着游戏速度走

全局变速（倍速战斗）对特效的含义是"发射频率和寿命同时改"，`Core/Component/Particle.ts` 把这件事封死在组件里：

```ts
public setSpeed(speed) {
    if (!this.data) this.init();
    const scale = isFinite(Number(speed)) && Number(speed) > 0 ? Number(speed) : 1;
    this.speed = scale;
    this.particle.speed = this.data.speed * scale;
    this.particle.speedVar = this.data.speedVar * scale;
    this.particle.life = this.data.life / scale * this.lifeScale;
    this.particle.lifeVar = this.data.lifeVar / scale * this.lifeScale;
    this.particle.emissionRate = this.data.emissionRate * scale;
}
```

速度正比放大、寿命反比缩短、发射率正比放大——粒子在变速下"长得一样快"，而不是慢动作。组件监听 `CoreEvent.GameSpeedChange` 自动同步。代码参数的粒子也走同一套约定：`MechanicalSmokeView` 的双层烟雾（core 48 粒 + outer 36 粒）全部参数写死在代码里，`intensity/burst` 只调 `emissionRate`——美术参数进代码，换来的是改动可 diff、可回滚。

## 五、上线前核对

- 逻辑层新增表现需求只准加 RenderCommand 类型，禁止在 Logic 里 `instantiate`/`play`
- 新特效先定生命周期类别（一次性/持续/拖尾/碎片），再选 Manager；持续型必须给 duration，靠续期而不是重建
- 入池前 `clear()` 复位是硬要求，跨场景 `clearDynamic` 全清；池键遵循 `"Effect_" + path` 约定
- 粒子组件挂 `Particle.ts` 走速度缩放，禁止直接改 `emissionRate` 绕过变速
- 高频碎片类特效必须设池上限，超限策略默认回收最旧
- 无渲染验证用 `NullCombatStageView` 断言命令序列，不启动 Cocos 场景
