## 一、问题：图标尺寸不一，撑破底框

物品栏、武器列表、奖励弹窗这类 UI，图标都是摆在一个固定大小的底框（格子）里。但美术给出的图标资源尺寸并不统一：有 101×90 的炮塔图，也有几十像素的小图标，还有接近方形的大图。如果直接摆进格子里，大图就会溢出底框，UI 直接穿帮。

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

## 五、小结

- 图标进格子：ImgFixedSize，一个 fixedSize 搞定，注意 TRIMMED + Trim 去掉透明边干扰。
- 组件由 SIZE_CHANGED 事件驱动，运行时换图、换布局都不需要手动刷新。
