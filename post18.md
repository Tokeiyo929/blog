---
title: EnhancedScroller使用说明文档
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---


本文讨论了 EnhancedScroller 组件的使用说明，涵盖组件特点、接口实现、制作方式、案例展示以及问题解决方法等内容。关键要点包括：​

1. 组件特点：具备开箱即用的丰富列表功能，支持无限循环列表、动态数据驱动，采用真正的 MVC 架构方案，可跳转到指定索引位置，对象数量能根据滚动区域大小动态增长，还有可选的对齐功能。​
1. 简单接口实现：提供了 UIListUtils.List 和 UIListUtils.UIGrid 两个方法，用于创建列表和网格布局，通过添加单元格激活器和刷新列表大小来实现列表展示。​
1. 横向列表制作方式：添加并设置 ScrollRect，包括删除不用组件、设置容器、调整对齐等；修改 Viewport 方便预览；制作 ItemRender 并修正排布和对齐问题；保存 ItemRender 到隐藏节点；在代码中显示对象。​
1. 竖向列表案例：以 UIOnlineGiftDialog_v2 为例，但未详细说明制作过程。​
1. 问题解决：针对上下未对齐问题，当设计高度与 ItemRender 高度不一致时，补全 bottom 值，确保 LayoutGroup 计算的数据完整。​
1. 附件内容：包含 EnhancedScrollerTest.zip 使用方法和 EnhancedScroller_User_Manual.pdf 用户手册。 ​
​

## 组件特点:

1. 开箱即用丰富的列表功能
2. 无限循环列表功能。
3. 动态数据驱动。
4. 真正的 MVC 架构方案。
5. 支持跳转到指定索引的位置。
6. 对象数量可根据滚动区域的大小动态增长，按需添加元素。
7. 可选的对齐（吸附）功能。

## 简单的接口实现​

```csharp
UIListUtils.cs​
/// <summary>​
/// var ap = UIListUtils.List(scrollRect,listData,cellWidth, updateView)​
/// ap.AddCellActivator(itemPrefab);​
/// ap.UpdateListSize();//刷新列表​
/// </summary>​
/// <param name="scrollRect"></param>​
/// <param name="listData"></param>​
/// <param name="cellWidth"></param>​
/// <param name="updateView"></param>​
/// <returns></returns>​
public static DefaultListAdapter List(ScrollRect scrollRect,IList listData,​
int cellWidth, Action<int, Transform> updateView)​
{​
var scroller = scrollRect.gameObject.GetOrAddComponent<EnhancedUI.EnhancedScroller.EnhancedScroller>();​
var delegater = new DefaultListAdapter(scroller, listData, cellWidth, updateView);​
return delegater;​
}​
​
​
/// <summary>​
/// var ap = UIListUtils.UIGrid(scrollRect,listData,cellSize,4,0, updateView)​
/// ap.AddCellActivator(itemPrefab);​
/// ap.UpdateListSize();//刷新列表​
/// </summary>​
/// <param name="scrollRect"></param>​
/// <param name="listData"></param>​
/// <param name="cellSize"></param>​
/// <param name="rowCount"></param>​
/// <param name="hSpacing"></param>​
/// <param name="updateView"></param>​
public static GridAdapter UIGrid(ScrollRect scrollRect,  IList listData,​
Vector2Int cellSize, int rowCount, int hSpacing, Action<int, Transform> updateView)​
```




## 制作方式:

案例制作一个横向列表​
1. 添加ScrollRect,重命名为srv_bag.​
    1.1 删除不用的组件.​
    ![飞书文档 - 图片](https://i.postimg.cc/DZPhv3xn/飞书文档_图片_1765257647.png)
    删除后:

  [![29fe0ea3_e023_4ee9_8e4c_58d61ffe280b.png](https://i.postimg.cc/DZJfnMtc/29fe0ea3_e023_4ee9_8e4c_58d61ffe280b.png)](https://postimg.cc/DJh3cBfW)

  1.2 设置ScrollRect的容器.

[![9ee161b6_c1ca_4aba_a0cb_3a87acd74911.png](https://i.postimg.cc/Qt9NhyRb/9ee161b6_c1ca_4aba_a0cb_3a87acd74911.png)](https://postimg.cc/CB0p4mMB)

1.3 设置Recttransform对齐.影响Item的对齐.​
![飞书文档 - 图片](https://i.postimg.cc/1trSm1v6/飞书文档_图片_1765257650.png)

2. 修改Viewport,方便预览列表效果.​
2.1 确保Viewport最大​
2.2 删除Viewport上脚本​
2.3 为Viewport添加HorizontalLayoutgroup组件.修正好HorizentalLayougroup属性​

[![80361a93_c87d_4a0c_a48e_5f5932ae5a15.png](https://i.postimg.cc/LXY42brf/80361a93_c87d_4a0c_a48e_5f5932ae5a15.png)](https://postimg.cc/ftsQvBWT)

[![872fdf63_5f53_4c87_a516_f677c7f2a8f5.png](https://i.postimg.cc/ydg6sbw0/872fdf63_5f53_4c87_a516_f677c7f2a8f5.png)](https://postimg.cc/WFVc7Xp4)



3. 制作ItemRender,预览列表排布.​
3.1 ​
![飞书文档 - 图片](https://i.postimg.cc/sX4zjCTv/飞书文档_图片_1765257653.png)
3.2 排布​

[![0d9a6f7a_7142_4831_8673_235eec1e3b1d.png](https://i.postimg.cc/TwL2f4Zb/0d9a6f7a_7142_4831_8673_235eec1e3b1d.png)](https://postimg.cc/sQzCJwff)

3.3 修正排布出界. 为ScrollRect添加Mask​

[![33b28e6b_7fd6_480a_be49_2f59339a21bc.png](https://i.postimg.cc/50Y9bRZC/33b28e6b_7fd6_480a_be49_2f59339a21bc.png)](https://postimg.cc/xJQVPtjf)


3.4 修正对齐问题.​

![飞书文档 - 图片](https://i.postimg.cc/nrVJMSWj/飞书文档_图片_1765257656.png)
![飞书文档 - 图片](https://i.postimg.cc/sX4zjCTp/飞书文档_图片_1765257658.png)
3.5 将设置信息设置到EnhancedScroller上.Viewport是会在运行时候被删除的.​


4. 保存ItemRender. 这里的做法是把ItemRender放入一个隐藏的节点下.并重命名为ref_BagRender​
![飞书文档 - 图片](https://i.postimg.cc/J07LtYFZ/飞书文档_图片_1765257661.png)
5. 代码中显示对象.​

   ```csharp
   var srv_bag = locator._G<ScrollRect>(nameof(UI.srv_bag));​
   if (srv_bag != null)​
   {
   	var ap2 = UIListUtils.List(srv_bag, bagData, 100, RenderBag);​
   ap2.AddCellActivator(locator._G((int)UI.ref_BagRender));​
   ap2.UpdateListSize();​
   }
   
   private void RenderBag(int index, Transform cell)
   {
   	var dataIndex = bagData[index];​
   var locator = cell.GetOrAddComponent<ComponentLocator>();​
   locator.Init(typeof(BagUI));​
   locator.SetText(BagUI.txt_name, dataIndex.Item2);​
   locator.SetText(BagUI.txt_lvl, dataIndex.Item1.ToString());​
   locator.ClickHandler(BagUI.btn_click, index, OnBagBtnClick);​
   }
   
   private void OnBagBtnClick(Transform tfm, int index)​{
   	var dataIndex = bagData[index];​
   UnityEngine.Debug.Log($"click bag index:{index},{dataIndex} :: {dataIndex.Item1},dataIndex:{dataIndex.Item2}");​
   }
   
   ```

   

最终效果:
![飞书文档 - 图片](https://i.postimg.cc/sxfr1HL4/飞书文档_图片_1765257664.png)
竖向的列表例子:
UIOnlineGiftDialog_v2​
问题集合:

1. 上下未对齐.设计高度为120,ItemRender高度为100,然后设置top为10.结果ItemRender平铺,高度110.​
解决方法: 补全bottom为10.这样高度就是100了.LayoutGroup设置children为拉伸,占满,所以最好确保计算的数据完整.​
附件: 使用方法,List/Grid​
附件: EnhancedScroller用户手册​

