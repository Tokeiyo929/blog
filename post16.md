---
title: RG UI搭建规范
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---

RG UI搭建规范​


本文讨论了RG UI搭建规范，涵盖了Prefab、图片、文本等方面的内容及制作要求。关键要点包括：​


1. 通用Prefab ：通用Prefab有特定目录，如通用按钮有5种颜色，程序有通用脚本；还有通用气泡、有标题和无标题弹窗等。​


1. Prefab制作规范 ：新系统搭建要做好区域划分和层级关系，按需建文件夹并新增AB名；已有系统替换要检查脚本引用，搭建后自查报错；脚本使用上，全屏界面标题和返回按钮可选，非全屏界面弹窗遮罩可选。​
1. 图片使用规范 ：常用EvonyImage，切图尽量小，通过拉九宫还原效果图；新系统图片资源要新建文件夹打图集并保存项目文件；替换已有系统在对应文件夹修改散图；大图放指定目录并设置ab名；避免在图片上加描边投影。​
1. 文本使用规范 ：常用EvonyText、LanguageText及Text，分别用于配置文本、固定文本（需填多语言Key）、渐变文本；描边和投影组件有暂定属性。​
1. 其他注意事项 ：Button、Slider等组件可使用unity自带，功能或设计问题及时沟通；所有UI资源都要选AB名。 ​

# 一. Prefab​


## 通用prefab​


### 目录：Assets\PackageRes\Raw\Category\Prefabs\UI\Common   ​


### 通用按钮： CommonBtn            目前一共5种颜色按钮 程序已写通用脚本，按钮是什么颜色，在Bg Index里填对应的事件序号，多语言Key填在Lan Key里​
![飞书文档 - 图片](https://i.postimg.cc/nchW82ny/飞书文档_图片_1765249077.png)

### 通用气泡：UIItemTip​
![飞书文档 - 图片](https://i.postimg.cc/kgrWNMhC/120X120.png)

### 通用有标题弹窗：UIPopupTipsDialog，UICommonWindow，UITwoButtonDialog​
![飞书文档 - 图片](https://i.postimg.cc/qvf2cBZd/850X850.png)



### 通用无标题弹窗：UICommonPop​
![飞书文档 - 图片](https://i.postimg.cc/VLkhygYm/飞书文档_图片_1765249082.png)





## prefab制作规范​


### 1.新系统搭建，先有一个基本的区域划分，理清层级关系，各区域都用空节点包起来，做好和父级停靠关系，方便适配和动效制作，新系统按需建立新文件夹，且需新增AB名，格式：prefab-ui-系统英文名。已有系统的新界面prefab需选择AB名​
![飞书文档 - 图片](https://i.postimg.cc/02y4gn8q/飞书文档_图片_1765249089.png)

### 2.已有系统替换，在替换完成后需检查父节点上的脚本的引用是否丢失，不能出现Missing，且搭建完成后需运行自查有无报错，有的话及时联系程序解决​


### 3.脚本的使用方法​


#### 全屏界面：标题和返回按钮在脚本上可选，并需填写Title Key​
![飞书文档 - 图片](https://i.postimg.cc/X7YPMLVj/飞书文档_图片_1765249090.png)



#### 非全屏界面：弹窗的遮罩在脚本上可选，无需单独设置​
![飞书文档 - 图片](https://i.postimg.cc/wTjrK26H/飞书文档_图片_1765249093.png)

# 二.图片​


## 目前项目常用EvonyImage​
![飞书文档 - 图片](https://i.postimg.cc/52c859kc/f32bc534_7758_427e_baa7_b57d70056afd.png)




### 1.图片的切图一定要尽量小，通过设置属性拉九宫来还原UI效果图。通用图集路径Assets\PackageRes\Raw\Category\UIAtlas\Texture\Common​


### 2.新系统图片资源需在Rg\UI\Sprite路径下新建文件夹，放入散图用texturepacker打图集，并把图集的项目文件保存在此处方便之后修改，详见​UI图集制作说明并导入unity后新建AB名，命名格式texture-该系统英文​
![飞书文档 - 图片](https://i.postimg.cc/nchW82HH/飞书文档_图片_1765249097.png)
![飞书文档 - 图片](https://i.postimg.cc/nh8qKVwf/ac8e680b_0880_4a43_a26f_aa81054702e7.png)


### 3.替换已有系统，在Rg\UI\Sprite下找到对应的文件夹和对应的tps文件，打开tps文件后在各系统的文件夹中直接修改/增加/删除散图，图集修改会自动生成在打开的tps项目里，最后生成图集并导入unity，保存图集项目，所有的修改一并提交。   ​


### 4.背景之类的大图直接放在Assets\PackageRes\Raw\Category\UISprite目录下，设置ab名ui-XXXX​


### 5..不要在图片上加描边投影，一律通过叠加两张图或者切图解决​


### 6.非按钮的图片此项关闭，除了背景​
![飞书文档 - 图片](https://i.postimg.cc/bNw5XgzY/飞书文档_图片_1765249100.jpg)

# 三.文本​


## 常用的有EvonyText、LanguageText及Text​


### 1.EvonyText常用于配置文本​

​



### 2.LanguageText用于固定文本，需要填多语言Key，Key值可以在Assets\Resources\Language\zh-CN.txt里搜索到​


### 注意：文本内不要出现中文​
![飞书文档 - 图片](https://i.postimg.cc/HskNGzps/飞书文档_图片_1765249103.png)

### 3.Text用于渐变文本，搭配TextGradient组件一起使用​

![飞书文档 - 图片](https://i.postimg.cc/vZR578SF/0f19d8d3_0960_4aab_bd4f_083b79055e28.png)



### 4.描边属性暂定1.5 无透明度​
![飞书文档 - 图片](https://i.postimg.cc/02y4gn8N/飞书文档_图片_1765249106.png)
投影组件暂定属性X 0  Y -2 透明度200​
![飞书文档 - 图片](https://i.postimg.cc/7ZvS1Ptp/b1f23588_b16b_443e_a474_9523ce503933.png)

# 四.其他注意事项​


## 其他组件如Button、Slider、ScrollView可使用unity自带，功能不明确或设计不合理时需及时和UI设计师、策划及程序及时沟通​


## 所有的ui资源，不管是图片还是prefab都需要选AB名​


## 其他详见：​RG_UI版本清单/规范    ​RG美术资源管理标准​


## ​

