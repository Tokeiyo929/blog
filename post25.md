---
title: 死亡结算改了五版：发奖即时、展示延迟，与动画和暂停彻底解耦
category: "[代码解析]"
date: 2026-11-23
project: 炮塔大作战
---

炮塔大作战的死亡结算前后改了五版（35 天）：等过死亡动画、拦过双击、防过重开污染，最终收敛成一条不变量——奖励即时持久化，面板延迟 0.5 秒展示且可取消，两者零共享状态。

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

11-19 的终版把这条路整个删掉，测试里直接用异常钉死：

```js
frame.getCurrentStage = () => ({
  waitForDeferredDeathAnimation() { throw Error('settlement must not wait for animation'); },
  endCombat() { ended++; }, exportBattleLogToClipboard() {},
});
```

测试名就是规范原文：**「暂停且死亡动画永不结束，先持久化再固定延迟展示」**——结算永远不许依赖动画完成。

## 三、终版不变量：发奖归发奖，展示归展示

终版的核心在 `settleBattleResult`（`Frames/GameFrame/GameFrame.ts`）。先看发奖，注释把定位写死了：

```ts
private settleBattleResult(resultFrame, isVictory, progress): void {
    // 进度、基础奖励和首通奖励在同一持久化事务内结算，界面仅展示结果。
    // 重试沿用同一 receipt，不能通过再次打开结果界面重领基础或首通奖励。
    if (!this.battleSettlementId) this.battleSettlementId = this.createBattleSettlementId();
    const result = SystemHelper.GetSystem(SysStage).settleBattle(
        this.currentStageType, this.currentStageId, progress, isVictory,
        () => this.getBattleRewardList(progress, isVictory), this.battleSettlementId);
    if (!result.ok) {
        this.retrySettlement = () => this.settleBattleResult(resultFrame, isVictory, progress);
        this.showSettlementRetry();
        return;
    }
    // ...组装 settleParam，关掉选卡/设置/复活三个界面
}
```

发奖在 `showBattleResult` 里**同步完成**，与任何动画、暂停无关；失败走重试且沿用同一 `battleSettlementId`，事务身份保证重试不会变成重领。展示则分成两条路：失败结算立即展示（玩家等复活流程已经够久了），胜利结算固定延迟：

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

延迟 0.5 秒只是给爆炸演出留个窗口，它**不等待任何东西**：到点就出，除非被取消。取消有双保险——回调身份比对（`settlementDisplayCallback !== display` 说明已被替换或清空）加局号比对（`battleSettlementId` 换了说明已经重开）。`resetBattleSession` 和 `onHide` 都会调 `cancelSettlementDisplay()`，重开一局或切后台，挂着的旧展示直接作废。

顺带补上设置面板的口子：`onBtnSetting` 在 `resultShowing` 时直接 return，设置面板已开着则强制隐藏——结算面板不再可能被设置界面盖住。

## 四、每版踩的坑，最终都变成守卫

五版迭代留下的守卫今天还在，各自盯着当年的坑：

- `resultShowing` 单闸门：`onLevelPass`/`onLevelFail`/`showBattleResult` 第一行全是它，双击、事件重放都进不来
- `reviveRequestVersion` 版本号：复活弹窗的广告回调迟到时，版本号对不上直接丢弃，复活链路"回调赛跑"的产物（10-21 引入，11-05 战车死亡时扩展到结算）
- `battleSettlementId` 事务身份：同局重试沿用、新局更换，重试重领和跨局污染都靠它挡
- `settlementDisplayCallback` 展示凭证：延迟展示的"取货凭证"，被取消或替换就失效

四个守卫没有一个是提前设计出来的，全是 bug 现场留下的护栏。真正提前想清楚的是 11-19 那次：**把"发奖"和"展示"拆成两个生命周期**，前者即时、不可取消；后者延迟、可取消。此前每一版的洞，根源都是把这两件事当成一件来调度。

## 五、坑钉进测试：9 种暂停组合的矩阵

终版同提交改了 `chapter-chest-settlement-isolation.test.cjs`（17 用例 86 断言），最狠的是把 boss 和暂停状态做成矩阵，三种暂停 × 三个 boss，全部假设死亡动画永不结束：

```js
for (const bossId of [1001, 1004, 1005]) for (const pause of ['选卡', '复活', '设置']) {
  await test(`Boss ${bossId} ${pause}暂停且死亡动画永不结束，先持久化再固定延迟展示`, async () => {
    // ...scheduleOnce 被替换成只记录，不执行
    assert.equal(ended, 1); assert.equal(f.reviveShowing, false);
    assert.equal(frameShows, 0); assert.equal(delay, 0.5);
    assert.equal(bag.getItemCount(901), 6);           // 奖励已入库
    assert.equal(stage.getProgress(StageType.Normal, 2), 100);  // 进度已持久化
  });
}
```

另有两类回归各占一条：重复触发（结算出来后再打 `onLevelPass`/`onLevelFail`/`onBtnSetting`，余额和面板数都不变）和重开取消（`resetBattleSession` 后旧回调作废、新局号生效、已发奖励保留）。战车死亡的演出数据也在同一天被钉进 `car-death-presentation.cjs`：爆炸音效一声、0.2/0.4 秒两波炮弹、震屏 2→1→2/3 衰减。

## 六、上线前核对

- 结算只允许两条展示路径：失败立即展示、胜利固定延迟 0.5 秒；禁止再引入"等动画/等网络/等暂停恢复"的第三条
- 发奖（`settleBattle`）必须在 `showBattleResult` 内同步完成；展示失败不发奖 = 事故
- 新增会盖住结算的界面（设置、选卡、复活之外的），必须在 `showBattleResult` 里显式 `hideFrame`
- 延迟展示的回调必须带双保险：回调身份 + `battleSettlementId`，且在 `resetBattleSession`/`onHide` 中取消
- 改动结算链路先跑 `chapter-chest-settlement-isolation.test.cjs`，新增暂停态要进矩阵

回头看，第五版并没有比第四版多写多少代码——删掉 `waitForDeferredDeathAnimation` 那条链路之后，剩下的守卫反而都变得各司其职。死亡结算这种"所有系统在这里交汇"的位置，尽早把不变量拆干净，比多打一个补丁值钱得多。
