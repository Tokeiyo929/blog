---
title: 图标适配只留一个参数：fixedSize 定边界，换图交给 SIZE_CHANGED
category: "[代码解析]"
date: 2026-11-26
project: 炮塔大作战
---

炮塔大作战的图标从 45×45 到 156×158 不等，要塞进 52×52、88×88 这类固定格子。9-11 的 `62b1940a` 一次提交引入等比缩放组件并接进第一处 UI，现在四处各声明一个 fixedSize（46/88/100/100）。这四个值后来动过两个。

## 一、挂组件之前：图多大就显示多大

WeaponItemCommon 在挂组件前有三个 icon 节点，尺寸 156×158、45×45、49×58，scale 全是 1。当时觉得这样合理——图就几张，美术给什么摆什么，顶多编辑器里拖一拖。可格子不跟着图走，奖励槽 88×88，品质底框 52×52，156×158 的图摆进去直接穿帮。

9-11 的 `62b1940a`「更新美术资源」把两件事捆在一个提交里：品质框 UI（img_Quality 52×52 底框 + img_Icon 101×90 图标）搭出来，适配组件 ImgFixedSize（`assets/Root/Script/Component/ImgFixedSize.ts`，第三方，作者 chenkai 2021.10.19）进仓库，UI 当天就挂上了适配。核心逻辑只有长边一条：

```javascript
// ImgFixedSize.ts 第三方组件，摘核心三行；onLoad 里挂了 SIZE_CHANGED 监听
onSizeChanged() {
  var max = Math.max(this.node.width, this.node.height);
  this.node.scale = this.fixedSize / max;
}
```

这条规则在网页端是标配：MDN 对 `object-fit: contain` 的定义是「被替换的内容将被缩放，以在填充元素的内容框时保持其宽高比」。长边压到限值，短边等比跟着，宁可留白不变形，两行算术就说完了。

## 二、40 撑了十八天：目测值要还账

这些值都写在 prefab 里，改起来不碰代码，但初值是目测的，两处后来都改过。GameFrame 当天挂两处 img_Icon，fixedSize 都是 40；9-29 `87872e0b` 把存活的那个调到 46，prefab 里 scale 从 0.396（40/101）重烘成 0.4554（46/101），底框留边从 6px 收到 3px。WeaponItemCommon 同日挂 140 又同日调到 100（`e8c1f493` → `092d9926`）。值对齐槽位设计尺寸的另两处，挂完就没再动过：

| 预制体 | fixedSize | 接入提交 | 值史 |
|---|---|---|---|
| GameFrame img_Icon | 46 | 09-11 `62b1940a` | 40→46（09-29） |
| WeaponItemCommon icon | 100 | 10-10 `e8c1f493` | 140→100（当天） |
| RewardFrame Item/icon | 88 | 10-12 `316703c0` | 未动，对齐 88×88 槽位 |
| LevelInfoItem icon | 100 | 10-20 `9a9f1782` | 未动，吴戈飞替换关卡 UI 时出生即挂 |

和手改尺寸比，这类调整只动 prefab 里的声明值，不碰代码；手改的话四处都得重拖一遍 scale。

## 三、量的是节点，节点带着透明边

缩放按 node.width/height 算，节点尺寸来自图片完整尺寸，包括四周透明像素——内容小、透明边大的图量出来偏大，缩完显得偏小。官方手册给了对照：Size Mode 的 TRIMMED「使用原始图片资源裁剪透明像素后的尺寸」，RAW 是「未经裁剪的尺寸」，勾选 Trim 则「在渲染时去除原始图像周围的透明像素区域」。项目里 img_Icon 的 sizeMode 就是 TRIMMED（HEAD 的 GameFrame.prefab 里 `_sizeMode: 1`）。

四处敢在出生时就挂上，靠的是事件侧：SIZE_CHANGED 驱动，运行时换品质、奖励弹窗按类型换图，`setSpriteFrame` 之后尺寸一变自动重算，调用方不用接任何东西。代价是组件接管了 node.scale，UI 动画再动同一个属性会冲突，项目里还没遇到。它也始终是第三方代码，没进维护线，全史只有 JJ 9-28 把 `@menu` 从 framework/ 挪到 Core/Component/ 一次整理；后续要加能力，得先决定是 fork 还是自己写。

## 参考

- [object-fit（MDN）](https://developer.mozilla.org/zh-CN/docs/Web/CSS/object-fit)
- [Qt Quick Image fillMode（Qt 6 文档）](https://doc.qt.io/qt-6/qml-qtquick-image.html)
- [Sprite 组件（Cocos Creator 2.4 手册）](https://docs.cocos.com/creator/2.4/manual/zh/components/sprite.html)
