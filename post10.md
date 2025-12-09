---
title: UIParticle使用
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---


UIParticle使用​
本文讨论了 UIParticle 的使用情况，包括其优缺点、当前 UI 特效处理方案、替换方案、属性说明、具体使用案例和常见问题。关键要点包括：​
1. UIParticle 优点：减少 Canvas 使用，降低性能开销；支持 Mask 裁切；简化层级理解成本；避免异步加载带来的 Layer 错乱问题。​
1. UIParticle 缺点：DrawCall 爆炸无法避免，尤其在同屏存在多个装备/品质框特效时影响性能。​
1. 当前 UI 特效处理方案：FXImage 支持 Mask 裁切但性能代价高、难以批量处理；Canvas + ChildCanvas + SortingGroup 渲染顺序可控但大量 Canvas 导致 DrawCall 爆炸、不支持 Mask 裁切。​
1. 替换方案：将 FXImage 组件替换为 PrefabHolder 脚本，统一管理特效加载与生命周期，引入 UIParticleSetting 配置，设置粒子缩放比例。​
1. 替换后优势：去除对 RenderTexture 依赖，减少 Camera 数量，可裁切，层级统一由 Transform 或 SortingGroup 控制，保持较好的批处理能力。​
1. UIParticle 属性说明：Scale 为缩放；PositionMode 有 Absolute（绝对位置）和 Relative（相对位置）两种；AutoScalingMode 主要用于屏幕自适应，有 None 和 Transform 两种模式。​
1. 常见问题解答：使用 UIParticle 后不需要 SpriteMask；粒子系统用 CustomData 显示异常需在 Canvas 添加通道对应 CustomData 数据。 ​
​

## ✅ 优点（现方案的优势）​

1. 减少Canvas使用​
1. 降低Canvas刷新带来的性能开销，避免频繁重建Layout与Batch。​
1. 支持Mask裁切​
1. 特效可以被Mask裁剪区域正确遮挡，符合UI设计需求。​
1. 简化层级理解成本​
1. 显示层级即显示顺序，规避了复杂的SortingOrder计算逻辑。​
1. 避免异步加载带来的Layer错乱问题​
1. 动态加载Prefab不再依赖特定Layer，降低表现异常的风险。​

## ❌ 缺点（当前处理方案的问题）​

- DrawCall 爆炸无法避免​
- 尤其在同屏存在多个装备/品质框特效时，如“45装备特效”，DrawCall激增，影响性能。​

## 📦 当前UI特效处理方案​


### 方案 1：FXImage（待替换）​

优点：​
- 支持 Mask 裁切​
- 层级控制简便，能处理特效在 UI 背后的渲染问题​
缺点：​
- 性能代价高：需要额外的Camera + RenderTexture，增加开销​
- 难以批量处理，打断UI渲染链，造成效率下降​

### 方案 2：Canvas + ChildCanvas + SortingGroup​

优点：​
- 渲染顺序可控，满足UI中前后层级的需求​
缺点：​
- 大量Canvas导致DrawCall爆炸​
- 不支持Mask裁切​
- 多特效场景DrawCall爆炸，难以控制​

## 🔁 替换方案：FXImage 替换计划​

`将FXImage组件替换为 PrefabHolder 脚本​`
- 统一管理特效加载与生命周期​
`引入 UIParticleSetting 配置​`
`设置粒子的缩放比例（scale）​`
1. 实现特效正确显示需满足三个条件：​
`Scale​`
`PositionMode​`
`AutoScalingMode​`
1. 关于 Scale 的计算：​
- 通常根据所在UI容器的宽度决定，例如：​
`品质框特效 = 宽度 / 4.0f​`
- 避免直接手动设置，保持自动适配​

## ✅ 替换后优势​

- 去除对RenderTexture依赖​
- 减少Camera数量​
- 可裁切（取决于UIParticle系统实现）​
- 层级统一由Transform或SortingGroup控制​
- 保持较好的批处理能力（部分情况）​

# UIParticle属性说明：​

Scale 就是缩放，不解释​




PositionMode（位置模式）​
Absolute（绝对位置）特效以自身为中心进行缩放​
Relative（相对位置）特效以UIParticle为中心进行缩放​
区别直接看下面例子，按需选择​
Absolute​
![飞书文档 - 图片](https://i.postimg.cc/hGqcsVc9/飞书文档_图片_1765238756.gif)
Relative​
![飞书文档 - 图片](https://i.postimg.cc/xTbwZqsZ/20250614142013_rec_(1).gif)


AutoScalingMode ​
主要用来做屏幕自适应，应对不同分辨率下的缩放，没有特殊需求就选None​
None 什么都不做​
UIParticle 会跟随UIParticle组件进行适应​
Transform 无论屏幕尺寸怎么变,特效本体都保持Scale = 1的状态(会跟随父物体的Scale进行缩放)​

# 具体使用案例：​

预制件名称：UISpHeroTaskReward​
需要修改的特效：​
![飞书文档 - 图片](https://i.postimg.cc/vmLMNDZp/飞书文档_图片_1765238760.gif)
## 具体步骤​


![飞书文档 - 图片](https://i.postimg.cc/SK7qvjxt/飞书文档_图片_1765238763.png)

![飞书文档 - 图片](https://i.postimg.cc/gk6C7rMH/bb5188e2_dcab_4c20_9668_d53d32998c2a.png)


![飞书文档 - 图片](https://i.postimg.cc/YSfksjCn/飞书文档_图片_1765238767.png)

![飞书文档 - 图片](https://i.postimg.cc/hGbg5htC/飞书文档_图片_1765238770.png)

![飞书文档 - 图片](https://i.postimg.cc/SNzBPjZd/c1862194_1285_46a1_898a_3d7b96704acd.png)

![飞书文档 - 图片](https://i.postimg.cc/GhsWf9MQ/0653de01_b71b_49d6_8624_9f7bd664ff2b.png)

![飞书文档 - 图片](https://i.postimg.cc/KYrFH4YF/飞书文档_图片_1765238774.png)

![飞书文档 - 图片](https://i.postimg.cc/wTsCr3WD/1d0c6310_880c_44f8_9c96_2d78e98e6cca.png)

![飞书文档 - 图片](https://i.postimg.cc/vB0yGj9g/飞书文档_图片_1765238776.gif)
大功告成​
常见问题:
1. 为什么SpriteMask的mask方式不生效了.​
1. 在使用UIParticle以后,特效属于Image类似的组件,直接受到Mask的影响.所以不需要SpriteMask​
1. 为什么粒子系统用CustomData以后,粒子特效显示异常.​
1. Canvas需要添加通道对应CustomData数据.否则对应通道没有数据,导致显示 异常.​
1. UICavans上默认添加了TEXCOORD1,TANG,NORMAL通道.​

---
