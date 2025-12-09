---
title: RG项目热更规范
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---




本文讨论了 RG 项目热更规范，包括代码调用规则、分组情况以及宏定义代码报错的解决办法。关键要点包括：​


1. 代码调用限制 ：非 Assets/Scripts 路径里的代码不可直接调用 Assets/Scripts 路径里的代码。​
1. 代码分组情况 ：Assets/Scripts 里的代码分三组，HOT 路径代码会热更，如 ui 窗口脚本；AOT 路径代码不热更，供 HOT 调用，如 ui 组件；其他代码不热更，可调用 HOT 和 AOT 代码，如热更新启动代码、工具代码。​
1. Editor 与 Runtime 代码调用规则 ：Editor 的代码可直接调用 HOT，Runtime 的代码不能直接调用 HOT，需用 HybridCLR 和 AI 配合的反射方法。​
1. 宏定义代码报错解决办法 ：有宏定义代码报错时，可手动添加引用，如切换到对应平台报错时按此操作。 ​

# 1.非Assets/Scripts路径里的代码不可以直接调用 Assets/Scripts路径里的代码​


# 2.Assets/Scripts里面的代码分三组：​

2.1.Assets\Scripts\HOT路径里的代码，会热更的代码；比如ui窗口脚本​
2.2.Assets\Scripts\AOT路径里的代码，不会被热更，会被HOT调用(依赖)的代码；比如ui组件​
2.3.Assets\Scripts其它代码，不会被热更，可以调用HOT的代码，可以调用AOT；比如热更新启动代码，工具代码​
2.4.Eitor的代码可以直接HOT,,Runtime的代码绝对不可以直调用Hot，只能用使用​HybridCLR和AI的配合使用提到的反射方法​

# 3.有宏定义代码报错，大家可以手动加一下引用：例子​
![飞书文档 - 图片](https://i.postimg.cc/htFPhkzn/fei-shu-wen-dang-tu-pian-1765242163.png)
例如这种，当切换到对应平台报错，可以手动加一下引用​
​![飞书文档 - 图片](https://i.postimg.cc/sxvDZy4G/850X850.png)
