---
title: 图片尺寸适配组件使用文档
category: [代码解析]
date: 2026-10-28
excerpt: 物品栏、奖励弹窗里的图标尺寸不一，超出底框就会穿帮。结合项目实际用例，讲清楚 ImgFixedSize、InsetByScale、FullByScale 三个缩放适配组件的原理与区别。
tags: [程序, UI]
---

## 一、问题：图标尺寸不一，撑破底框

物品栏、武器列表、奖励弹窗这类 UI，图标都是摆在一个固定大小的底框（格子）里。但美术给出的图标资源尺寸并不统一：有 101×90 的炮塔图，也有几十像素的小图标，还有接近方形的大图。如果直接摆进格子里，大图就会溢出底框，UI 直接穿帮。

![游戏内效果：不同尺寸图标都限制在格子内](images/img_021_001.png)

解决思路就一句话：**图片超过限制尺寸时，等比缩放到限制以内**。

## 二、原理：长边压到固定值

取节点宽高中较长的一条边，把长边缩放到 `fixedSize`，另一条边等比缩小：

```javascript
let node;         // 图片node
let fixedSize;    // 限制大小
var max = Math.max(node.width, node.height);
node.scale = fixedSize / max;
```

以项目里的实际数据为例：GameFrame 的品质底框 `img_Quality` 是 52×52，里面的图标 `img_Icon` 原始尺寸 101×90，组件设置 `fixedSize = 46`：

scale = 46 / 101 ≈ 0.455，缩放后图标约 46×41。无论图标原始比例是多少，长边都不超过 46，稳稳落在 52×52 的底框内；而短边只会比长边更小，天然不会超出。

## 三、ImgFixedSize 组件

组件位于 `assets/Root/Script/Component/ImgFixedSize.ts`，挂在图标节点上：

```javascript
const { ccclass, property, menu } = cc._decorator;

/**
 * 图片适配大小
 * @author chenkai 2021.10.19
 */
@ccclass
@menu("Core/Component/ImgFixedSize 图片固定尺寸")
export default class ImgFixedSize extends cc.Component {

    @property({ type: cc.Integer, tooltip: "固定尺寸" })
    public set fixedSize(value) {
        this._fixedSize = value;
        this.onSizeChanged();
    }

    public get fixedSize() {
        return this._fixedSize;
    }

    @property({ type: cc.Integer, tooltip: "固定尺寸" })
    private _fixedSize: number = 1;

    onLoad() {
        this._fixedSize = this.fixedSize;
        this.node.on(cc.Node.EventType.SIZE_CHANGED, this.onSizeChanged, this);
        this.onSizeChanged();
    }

    /**当尺寸变化时，重置node节点大小 */
    onSizeChanged() {
        var width = this.node.width;
        var height = this.node.height;
        var max = Math.max(width, height);
        this.node.scale = this.fixedSize / max;
    }
}
```

两个值得注意的实现细节：

1. **监听 SIZE_CHANGED，而不是只在 onLoad 算一次**。图标经常是运行时动态换的（换皮肤、换品质、奖励弹窗按奖励类型换图）。`setSpriteFrame` 之后节点尺寸变化，SIZE_CHANGED 触发，自动重新缩放，调用方完全不用关心适配这件事。
2. **property 的 setter 里也调了一次 onSizeChanged**。在编辑器里调 `fixedSize` 参数时立刻能看到缩放效果，不用进游戏验证。

![WeaponItemCommon 的 icon 节点挂 ImgFixedSize，固定尺寸 = 100](images/img_021_002.png)

项目里的使用位置：

| 预制体 | 节点 | fixedSize | 场景 |
|---|---|---|---|
| WeaponItemCommon | icon | 100 | 武器列表图标 |
| RewardFrame | Item/icon | 88 | 奖励弹窗物品图标 |
| GameFrame | img_Quality/img_Icon | 46 | 品质底框内的炮塔图标 |
| LevelInfoItem | icon | 100 | 关卡信息图标 |

## 四、一个容易踩的坑：透明边

缩放按节点的 width/height 计算，而节点尺寸来自图片的**完整尺寸**——包括四周的透明像素。如果图标内容很小、周围一圈透明，量出来的尺寸会比肉眼看到的大，缩放后图标显得偏小。

解决办法：Sprite 的 SizeMode 设为 TRIMMED 并勾选 Trim，让节点尺寸取"裁掉透明像素后"的有效大小。项目里的图标纹理导入设置 `trimType` 默认就是 auto，配合 TRIMMED 使用即可。

![Sprite 的 SizeMode / Trim 设置](images/img_021_003.png)

## 五、延伸：相对目标节点适配

ImgFixedSize 是"绝对尺寸"思路：不管别的东西，长边压到写死的 fixedSize。但有一类需求它覆盖不了——**弹窗要适配各种屏幕比例**（小游戏平台机型五花八门），内容该缩多少取决于目标容器的大小，而不是一个固定数字。

项目里对应的两个组件，位于 `assets/Root/Script/Core/Component/`：

**InsetByScale 缩放嵌入**——保证整个节点都在目标范围内（等比 contain）：

```javascript
private scaleNode() {
    this.node.scale = MathUtil.min(
        this.target.width * this.target.scaleX / this.node.width,
        this.target.height * this.target.scaleY / this.node.height
    );
}
```

取宽、高两个方向缩放比的**较小值**，两个方向都不会超出 target。RewardFrame 等十余个全屏弹窗的 container 节点都挂了它，target 指向弹窗根节点——屏幕比例再怎么怪，弹窗内容都完整地嵌在背景里。

**FullByScale 缩放填充**——保证铺满目标，允许超出（等比 cover）：

```javascript
private scaleNode() {
    if(this.isWidth){
        this.node.scale = this.target.width * this.target.scaleX / this.node.width;
    }else{
        this.node.scale = MathUtil.max(
            this.target.width * this.target.scaleX / this.node.width,
            this.target.height * this.target.scaleY / this.node.height
        );
    }
}
```

取**较大值**，至少一个方向铺满 target。MainFrame 的 Center 节点挂了 FullByScale 且 `isWidth = true`，按屏幕宽度撑满，高度自然延伸。

三个组件放在一起对比：

| 组件 | 缩放依据 | 行为 | 项目用例 |
|---|---|---|---|
| ImgFixedSize | 固定数值 fixedSize | 长边压到固定值 | 武器 / 奖励 / 品质图标 |
| InsetByScale | 目标节点 | 完整嵌入（contain） | 弹窗 container 适配屏幕 |
| FullByScale | 目标节点 | 铺满填充（cover） | 主界面 Center 按宽铺满 |

还有个容易忽略的区别：InsetByScale / FullByScale 监听的是 **target** 的 SIZE_CHANGED（容器变了，内容跟着重算），而 ImgFixedSize 监听的是**自己**（图变了，缩放跟着重算）。监听谁，取决于"谁变了需要重算"。

![弹窗在不同分辨率下的适配效果](images/img_021_004.png)

## 六、小结

- 图标进格子：ImgFixedSize，一个 fixedSize 搞定，注意 TRIMMED + Trim 去掉透明边干扰。
- 内容进容器：InsetByScale 保证不超出，FullByScale 保证必铺满。
- 三个组件都由 SIZE_CHANGED 事件驱动，运行时换图、换布局都不需要手动刷新。
