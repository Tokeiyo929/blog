---
title: 血条分几段是画的事：快照只传 hp/maxHp，渲染侧除法自己算
category: "[代码解析]"
date: 2026-11-26
project: 炮塔大作战
---

炮塔大作战的 boss 血量上万，一根血条看不出打到了第几管。这条多层血条前后改了三版：phase 字段进过快照、33 天后整删；彩虹色轮换换成三张分段图；分段从「每管 1000 血」改成固定 100 管。改到最后，快照只传 hp/maxHp，分几段是渲染侧用除法算的。

## 一、phase 进过快照：三十三天的弯路

boss 血条不是第一个碰到「分阶段」的 UI。9 月的 `9c790168`（09-18「新增 盾牌兵二阶段换spine」）为盾牌兵的二阶段变形态，给 `EntitySnapshot` 加了 `phase` 字段（注释写着「当前血条/形态阶段，0-based」），`EntityView` 上配「阶段节点」数组和「阶段受伤变色动画」数组，`syncPhase` 在快照变化时切骨架。当时觉得这样合理：盾牌兵是唯一的二阶段怪，给「阶段」留一条快照到渲染的通用通道，下一个多阶段怪直接复用。

结果通道等了 33 天没等到第二个用户。10-21 的 `08271c98`（「废弃多阶段血条设计」）把它整体拆掉，`EntityView` 一个 diff 清掉 46 行。回头看问题出在注释那句话里——「血条/形态阶段」搅在同一个字段：快照每帧复制它，逻辑层负责推进它，prefab 上还得配好节点数组，三方为一个实际上只有盾牌兵在用的概念立了协议。血条分几段、怪换什么形态，拆开看都是画的事；揉进快照，改一次设计就要动逻辑层。

## 二、boss 血条三版：假分段怎么活下来的

boss 多层血条走了另一条路，第一版就没碰快照。10-15 的 `1efc00be`（「子母弹子弹，boss多层血条」）把 boss 血量按每管 1000 做除法，当前管序号、管内剩余比例全部现算，运行时克隆一根副条当「下一管」预览，配七个彩虹色按管序号取模轮换：

```typescript
const BOSS_HEALTH_BAR_UNIT_HP = 1000;
const totalBarCount = Math.floor(maxHp / BOSS_HEALTH_BAR_UNIT_HP);
const activeBarIndex = Math.floor((maxHp - hp) / BOSS_HEALTH_BAR_UNIT_HP);
const activeColor = BOSS_HEALTH_BAR_COLORS[activeBarIndex % BOSS_HEALTH_BAR_COLORS.length];
// ...当前管内剩余血量算出 activeBarRatio
this.progressBar.progress = activeBarRatio;
this.setFillColor(this.progressBar, activeColor);          // 直接改 barSprite 的 node.color
```

当时没真建几十根管，是算过账的：boss 配置血量是万级，prefab 上建几十个进度条节点配不动，而渲染侧从 maxHp/hp 算分段，快照和配置零改动。这版留下两个坑。第一个是克隆副条：`22514095`（10-20「修改了boss血条」）发现克隆出来的节点挂错了父节点、还带着背景图，血条叠层全乱，diff 里专门补了注释「Both fills must render after the shared background and before the current fill」，手动 `setSiblingIndex` 压到正确层级、关掉克隆带出的背景 sprite。第二个是彩虹色本身：美术看了说颜色没有语义，出了 3 张分段条纹理（`assets/Frames/FrameGame/Texture/new/1.png` 到 `3.png`），同一提交把改颜色换成了按管序号取模换图。

第三版改的是分段的来源。`b9e3a556`（10-21「替换了3选1特效」）把「每管固定 1000 血」翻转成「固定 100 管」：

```typescript
const BOSS_HEALTH_BAR_COUNT = 100;
const hpPerBar = maxHp / BOSS_HEALTH_BAR_COUNT;
const activeBarIndex = Math.min(BOSS_HEALTH_BAR_COUNT - 1,
    Math.max(0, Math.floor((maxHp - hp) / hpPerBar)));     // 两头 clamp 防越界
```

翻转的理由在两天后的 `51aa0f08` 里写得明白：boss 关卡要运行时覆写怪物血量（`BossDependencies` 的注释「Boss 运行时副本可覆盖血量，绝不改地图默认怪物或全局武器数值」）。每管 1000 血时，覆写一次血量，管数就跟着 maxHp 跳变；固定 100 管后段数恒定，改血量只改每管的血。分层之外的两个细节也活到了终版：副条预览让换管不跳帧，剩余管数用「x N」计数压在条上。

## 三、引擎本来就只给一根条

这套做法没发明新东西。Cocos 引擎源码 `cocos/ui/progress-bar.ts` 里，ProgressBar 组件的 progress 就一个 `@range([0, 1])` 的比例值，类注释写着「进度条组件，可用于显示加载资源时的进度」——引擎层不存在分段血条这个概念。Unity 那边同构，uGUI 的 `Image.fillAmount` 文档原句："0-1 range with 0 being nothing shown, and 1 being the full Image"。两家引擎都只有一根 0 到 1 的条，分段数是上层 UI 自己除出来的；快照里真正需要的，也只有 hp/maxHp。

代价记两条：固定 100 管意味着血量几百的低配 boss 也会被切出 100 管，视觉上瞬时掉一整管，目前项目里 boss 血量都在几千以上没触发，算遗留观察项；副条是运行时 `cc.instantiate` 出来的，首次显示才有这笔开销，prefab 里不占节点。phase 那条弯路也留了痕迹——后来再有人说「给快照加个字段」，我们先问一句：这是逻辑事实，还是画的事。

## 参考

- [Cocos Creator 引擎源码 progress-bar.ts（GitHub）](https://github.com/cocos/cocos-engine/blob/v3.8.2/cocos/ui/progress-bar.ts)
- [Unity uGUI 手册：Image.fillAmount（Unity 文档）](https://docs.unity3d.com/Packages/com.unity.ugui@2.0/api/UnityEngine.UI.Image.html)
