---
title: 图文混排制作使用
category: [代码解析]
date: 2025-12-03
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---




1.制作image_Font​

![飞书文档 - 图片](images/img_011_001.png)
![飞书文档 - 图片](images/img_011_002.png)
选中需要的图片或者文件夹点击build​
![飞书文档 - 图片](images/img_011_003.png)

2.创建emoji文本


![飞书文档 - 图片](images/img_011_004.png)

![飞书文档 - 图片](images/img_011_005.png)
​3.使用方式

![飞书文档 - 图片](images/img_011_006.png)
![飞书文档 - 图片](images/img_011_007.png)
![飞书文档 - 图片](images/img_011_008.png)
:hero_fragments_1006003:                      ：图片名字：​


ttTestText.text = LocalizationManager.Instance.GetString("player_info_65") + ":hero_fragments_1006003:300";​





