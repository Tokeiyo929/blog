---
title: 逻辑和表现解耦：死亡回调不等动画，只认固定延迟
category: "[代码解析]"
date: 2026-11-23
project: 炮塔大作战
---

炮塔大作战的死亡结算前后改了五版（35 天）：先后等过死亡动画、拦过双击、防过重开污染，最终收敛成一条不变量——奖励即时持久化，面板延迟 0.5 秒展示且可取消，两者零共享状态。

## 一、死亡从来不是一个事件

把 `GameFrame.ts` 里死亡结算相关的提交按时间排开，就是一部踩坑史：

| 日期 | 提交 | 想解决的问题 | 留下的坑 |
| --- | --- | --- | --- |
| 10-15 | `fc78fb69` 延续死亡机制实现复活 | 死亡给复活机会，看广告续命 | 死亡有了两条出路，复活失败才进结算 |
| 10-19 | `7eefebea` 首通独立奖励与章节宝箱事务结算 | 奖励不能重复领 | 结算成了持久化事务，需要身份标识 |
| 10-26 | `f77b51e3` boss死亡后结算游戏 | 让玩家看完整爆炸再出面板 | 面板开始等死亡动画，时序被动画绑死 |
| 11-05 | `b77fcfc9` 战车死亡结算 | 战车爆炸演出、防双触发 | 结算与复活弹窗、广告回调互相赛跑 |
| 11-19 | `255ec5b3` 死亡结算 | 把前四版的坑一次收口 | —— |

难点不在"弹个结算面板"，而在死亡时刻**同时**挂着四件事：boss 的死亡动画、可能的复活弹窗、选卡界面、玩家随时可能点的设置按钮。任何一件的状态都会影响面板该不该出、什么时候出。前四版的做法是把这四件事串成一条时序链，每版补一个洞，洞又在别处漏。

## 二、最贵的一课：面板等动画

10-26 的版本最有代表性。为了让胜利面板不遮住 boss 爆炸，我们让结算等死亡动画播完：

```ts
public waitForDeferredDeathAnimation(onComplete: () => void): boolean {
    return !!this.stageView && this.stageView.waitForDeferredDeathAnimation(onComplete);
}
```

`onLevelPass` 里先问动画，动画没在播就直接出面板，在播就注册回调等它播完。单看每一个分支都合理，合起来是灾难：**动画完成是渲染层的事，结算该不该出现是逻辑层的事**。boss 死亡瞬间若停在选卡、复活、设置任意一个暂停态，动画可能永远不会"播完"，结算面板就永远不出来——而且发奖也跟着动画一起被挂起了。

11-19 的终版把这条路整个删掉，并在测试里用异常把「结算不许等动画」钉死。测试名就是规范原文：**「暂停且死亡动画永不结束，先持久化再固定延迟展示」**。

## 三、终版不变量：发奖归发奖，展示归展示

终版的核心在 `settleBattleResult`（`Frames/GameFrame/GameFrame.ts`）。发奖在 `showBattleResult` 里**同步完成**，与任何动画、暂停无关：进度、基础奖励、首通奖励在同一持久化事务内结算；失败走重试且沿用同一 `battleSettlementId`，事务身份保证重试不会变成重领。展示则分成两条路：失败结算立即展示（玩家等复活流程已经够久了），胜利结算固定延迟：

```ts
// 发奖已持久化；短延迟只控制展示，不依赖死亡动画或战斗暂停状态。
const settlementId = this.battleSettlementId;
const display = () => {
    if (this.settlementDisplayCallback !== display || this.battleSettlementId !== settlementId) return;
    this.settlementDisplayCallback = null;
    this.showSettlementFrame(resultFrame, settleParam, settlementId);
};
this.settlementDisplayCallback = display;
this.scheduleOnce(display, VICTORY_RESULT_DELAY);  // 0.5s
```

延迟 0.5 秒只是给爆炸演出留个窗口，它**不等待任何东西**：到点就出，除非被取消；取消有双保险（回调身份比对 + 局号比对），重开一局或切后台，挂着的旧展示直接作废。

把结算时序和动画切开——这套做法也不是我们头一次见，**逻辑与表现解耦是成熟引擎的老架构**：Doom 的游戏逻辑按 35Hz 固定 tic 推进，渲染帧率完全独立（id Software 1997 年开源的源码至今如此）；Minecraft 的世界逻辑固定每秒 20 tick，帧率再高模拟步进也不动。落到"死亡后延迟展示"这类时序上，Godot 把 `call_deferred()` 和一次性 `create_timer()` 做成引擎级 API，我们用的 Cocos Creator 同理：`scheduleOnce` 挂固定延迟，而不是等动画播完。动画回调适合表现层接力（爆炸音效、镜头震动），不适合逻辑层裁决（该不该发奖、该不该弹面板）。

五版迭代留下的守卫今天还在——`resultShowing` 单闸门、`reviveRequestVersion` 版本号、`battleSettlementId` 事务身份、`settlementDisplayCallback` 展示凭证——没有一个是提前设计出来的，全是 bug 现场留下的护栏；想法也落进了测试，`chapter-chest-settlement-isolation.test.cjs`（17 用例 86 断言）把三种暂停 × 三个 boss 做成矩阵，全部假设死亡动画永不结束，断言奖励已入库而面板数为 0。

回头看，第五版并没有比第四版多写多少代码——删掉 `waitForDeferredDeathAnimation` 那条链路之后，剩下的守卫反而都变得各司其职。真正提前想清楚的是把"发奖"和"展示"拆成两个生命周期：前者即时、不可取消，后者延迟、可取消——此前每一版的洞，根源都是把这两件事当成一件来调度。终版之后只守一条铁律：结算只许两条展示路径（失败立即、胜利延迟 0.5 秒），第三条（等动画/等网络/等暂停恢复）谁都不许加。死亡结算这种所有系统都要来碰一下的地方，尽早把不变量拆干净，比多打一个补丁值钱得多。

## 参考

- [id-Software/DOOM（GitHub）](https://github.com/id-Software/DOOM)：游戏逻辑按 35Hz 固定 tic 推进，与渲染解耦
- [Tick - Minecraft Wiki](https://minecraft.wiki/w/Tick)："The game normally runs at a fixed rate of 20 ticks per second"
- [Object.call_deferred - Godot 文档](https://docs.godotengine.org/en/stable/classes/class_object.html)：方法调用延迟到帧末空闲时间执行
