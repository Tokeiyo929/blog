---
title: 合批优化先数后删：Mask 不裁东西，也在付模板缓冲的钱
category: "[代码解析]"
date: 2026-11-27
project: 晨光计划
---

《晨光计划》的性能战役还在继续。采样指认的 CPU 热点逐个落地之后，轮到了渲染侧。11-27 下午一条提交 `7091135`「删除无意义mask」，+1921/-2581 净删 660 行，没有新增渲染逻辑——删掉的是 28 个组件里的 19 个。

## 一、垫片把 28 个 Mask 搬了进来

项目从 Unity 迁 Cocos 时留了个垫片组件 SourceMask：prefab 里只存一份声明，运行时 configure() 再挂真正的 cc.Mask——矩形的走 Graphics 画裁剪框；勾了 showMaskGraphic 的走 SPRITE_STENCIL，挂一张 alphaThreshold=0.001 的 Sprite 当模板形状，还要生成一个 SourceMaskGraphic 背景子节点。12 个 prefab 清点出 28 处。

Cocos 官方文档《2D 渲染组件合批规则说明》写得直白：「内置组件 Mask、Graphics 和 UIMeshRenderer 组件由于材质不同和数据组织方式的差异，无法与其他组件合批」。Mask 的工作机制是模板缓冲——《Mask（遮罩）组件参考》：「在 Type 为 SPRITE_STENCIL 时，Mask 组件会添加 Sprite 组件，该 Sprite 组件会为模板提供形状」。

问题在于迁移之后内容变了。PageMonster 里 Slider 血条的 Value_Fill 挂着 Mask，下面 0 个子节点。Mask 只裁子节点，自己那张图不受影响，裁的是空气。PageModeOverlays 里 GameEnd_old 整组废弃面板还挂着 Mask。还有几处的裁剪活儿已被 SourceSlicedFill 接管，fill 直接画出来。28 个 Mask 每帧照付模板缓冲，还照断批。

## 二、删谁：决策函数，不靠眼睛看名字

上午先走正向合并，把静态 sprite 按连续批合并、跳过不可见、合并重复的 batch states——其中两笔 merge 类提交后来被 Revert，提交本体已不在仓库历史里，`b0c4c6f5` 的提交说明里留着这串尝试的记录。合并是在把打散的批拼回去，打散的源头没动。

下午换成减法。tools/analyze_batching.js 静态清点 prefab 里的合批破坏者，analyze_render_order.js 按渲染顺序模拟纹理切换次数。删除标准写成决策函数，一行定生死：

```js
if(clipsOfferOutline||!(mask.sourceEnabled===false||hasFill||!node._children.length||legacyOffer))continue;
```

四选一才删：Mask 已被关掉、SourceSlicedFill 已接管、下面没有任何子节点、挂在 PageModeOverlays 里的 Remove_AD_All 面板上；守卫是裁剪框里的轮廓图还可见就不删。

删之前先留了证据链。round-11 脚本把 SourceMask 逐个装回去截图对比：MinePack 的裁剪真有效果，回填保留。round-09 跑完 20 个场景的 before/after 截图回归，validate-prefabs.mjs 校验结构：__id__ 引用全部可解析、节点数和按钮数不变、组件归属一致。结果是 19 删 9 留。

## 三、同一个提交里顺手修了置灰

同一个提交里还把地图按钮的置灰改了。原来的两条路都在断批：sprite.grayscale 走的是引擎源码里 `set grayscale → changeMaterialForDefine()`，灰度是个材质开关，切材质即断批——对应官方合批条件「材质相同是合批的必要要求」；另一条路异步换预灰贴图，官方对贴图的说法是「贴图源以及贴图采样相同……一般情况下该条件是影响合批最主要的因素」。

换法只有四行：CommonButton 里一个静态的 disabledTint，加一个 `setTint`——`sprite.color = enabled ? Color.WHITE : CommonButton.disabledTint`。顶点色变了，材质和贴图没变。round-10 在运行时实测：两个 sprite 共享一张贴图，只把其中一个置灰，director.root.batcher2D.batches 仍是同一个批次。

## 心得

16:25 删完 Mask，17:51 SourceSlicedFill 重写接管 progress 遮罩，20:05 再打磨——删除之后紧跟接管。真机 drawcall 数字还要等验收，这次的验收标准是模拟器截图回归加批次实测。先数再删，删除要有决策函数和回放截图兜着。
