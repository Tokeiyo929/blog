---
title: UI 开发流程
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---


UI 开发流程​

本文讨论了 UI 开发流程、UI 面板制作、节点命名与绑定以及 UISystem 代码结构等方面的内容。关键要点包括：​


1. UI 开发架构模式：采用 MVVM 模式，View 根据数据刷新界面，通过 ViewModel 获取数据；ViewModel 处理业务逻辑并提供数据接口；Model 定义数据结构和存储数据；Service 负责网络通信。​
1. UI 面板制作：Prefab 路径为 Assets/PackageRes/Raw/Category/Prefabs/UI，各模块自建子目录；面板根节点添加 ComponentLocator 管理 UI 引用，可自动生成绑定代码。​
1. 规范化节点命名：注意 ref vfx 不搜索子节点，嵌套搜索时父节点不用该前缀，tfm 更通用，ref 用于自定义组件。​
1. 自动绑定节点：UI 界面未搭建时，在 BuildIn_keys 预先填写组件名可自动注入生成代码；界面已存在时，修改命名后点自动注入可生成绑定代码。​
1. 代码使用：View 必须继承 IView 接口和 PopupWindow 或 Dialog，预制体挂载 ComponentLocator，通过 Locator._G<T>(index) 获取组件。​
1. UISystem 代码结构：新增界面代码路径为 Assets/Scripts/HOT/UISystems，Model 包括 Data 和 Repository，View 处理 UGUI 相关，ViewModel 封装业务逻辑，Service 负责网络数据请求。​
1. 注意事项：自动生成代码时需确保 Locator 上有继承 IView 的界面脚本，否则编译会报错。 ​

# 架构模式 MVVM​
![飞书文档 - 图片](https://i.postimg.cc/TPR3VBVp/飞书文档_图片_1765246746.jpg)
1. View  根据数据刷新显示界面​
   1. 使用 ComponentLocator  收集界面UI组件​
   1. 通过ViewModel获取数据，显示界面​
1. ViewModel  处理界面业务逻辑，提供接口给View 去获取数据 ​
   1. 建议View不要直接访问Model层，应改为ViewModel层提供函数去访问数据返回给view​
   1. 界面简单没有ViewModel层，也可以访问Model​
   1. View层监听ViewModel事件，刷新界面​
      1. 事件触发，尽量在关键功能变化时触发​
      1. 避免仅某一个字段变化就触发事件，进行大量刷新​
      ​
1. Model  定义数据结构，仓库存储全局数据​
   1. 界面需要的数据，集中管理​
   1. 当数据变化时，触发事件，ViewModel层监听并处理​
      1. VM 处理数据后，将事件继续触发，抛给View层​
      ​
1. Service 定义网络通信​
   1. 与服务器交互，发送网络请求，处理服务器网络消息​
![飞书文档 - 图片](https://i.postimg.cc/V6ZvL4bm/1280X1280.jpg)


# UI面板制作​


## Prefab路径​

`Assets/PackageRes/Raw/Category/Prefabs/UI​`
各模块自建子目录：skil​
![飞书文档 - 图片](https://i.postimg.cc/vmQZrCrx/飞书文档_图片_1765246749.png)


## 添加组件 ComponentLocator  ​

面板根节点需要添加组件收集器，统一由它管理UI的引用，不要在View面板上公开变量，不要直接拖拽​
ComponentLocator  ​
- UI组件收集定位器，统一管理访问预制体Prefab上的UI组件​
- 可以自动生成绑定代码（目前是枚举，后续可扩展更多预先代码）​
- 自动搜索合规命名节点，一键自动注入，持有引用，运行时按索引访问​
![飞书文档 - 图片](https://i.postimg.cc/Pqt5W0WL/飞书文档_图片_1765246752.png)
默认无数据​


![飞书文档 - 图片](https://i.postimg.cc/8C1zRxRJ/飞书文档_图片_1765246755.png)

## 规范化节点命名​

注意 ref vfx 目前是不会搜索子节点，如果嵌套搜索，父节点不要用ref  vfx 前缀​
使用tfm 更通用些，ref 用于自定义组件（ref通常自己本身也会挂locator）​
![飞书文档 - 图片](https://i.postimg.cc/JnrHhG65/a278a373_9e5a_49cb_bd9a_357a5dfe68ec.png)
![飞书文档 - 图片](https://i.postimg.cc/jqfZf1ZW/飞书文档_图片_1765245463.png)


## 自动绑定节点​


### UI界面未搭建（程序比美术先做）​

在BuildIn_keys 预先填写需要的组件名，再点自动注入，也会生成预先填写的组件名枚举​
- 会提醒你，目前面板还没有这些节点​
- 点确定后，会自动生成代码​
注意：这里默认是认为Locator上有一个继承了 IView 的界面脚本的，这个界面名（也是类名）就是节点名​
去掉_ 前缀的后留下的名字​
![飞书文档 - 图片](https://i.postimg.cc/GpcmF6Fy/飞书文档_图片_1765246759.png)
![飞书文档 - 图片](https://i.postimg.cc/25FBm4wK/0bcbb2b1_8b26_412e_ac24_86c271eb362b.png)
如果仅有Locator，没有挂对应命名的View脚本，自动生成代码后，编译会报错，类似如下​
![飞书文档 - 图片](https://i.postimg.cc/YSpC6T6Y/飞书文档_图片_1765246761.png)


### UI界面已存在（美术已经拼完）​

程序后置，界面已拼接完成​
- 修改命名后，点自动注入​
- 绑定的枚举值会自动生成代码，写入到固定路径下​
![飞书文档 - 图片](https://i.postimg.cc/nLHh4N4m/飞书文档_图片_1765246764.png)
![飞书文档 - 图片](https://i.postimg.cc/qRJ67zbc/91a8008e_ddb4_4c12_928b_fe8e96b58090.png)
## 代码使用​

View 必须继承 IView  接口（它背后已经继承了 ILocatorOwner）​
目前有一个文档 ​UI 开发流程​
​UI 开发流程​




并继承  PopupWindow 或者 Dialog​
预制体挂载了脚本 ComponentLocator ​
![飞书文档 - 图片](https://i.postimg.cc/LsH8tGtj/飞书文档_图片_1765246767.png)
#### 获取任意类型组件​

`Locator._G<UITeamSkillSlotView_v2>((int)UI.ref_MainSkillSlot1)​`
- 使用 Locator._G <T> （index）​
- T 是组件类型​
- index 是自动生成的枚举类型​

#### 常用修改组件值​

Component_EXT2.cs  与 Component_EXT.cs  自行扩展常用接口​
继承了​

![飞书文档 - 图片](https://i.postimg.cc/43bhZz5F/18a142db_87e0_4ebf_ab24_18a3f942222f.png)
- 设置显示隐藏​
![飞书文档 - 图片](https://i.postimg.cc/mrbgYKYS/飞书文档_图片_1765246770.png)

- 设置文本内容​
![飞书文档 - 图片](https://i.postimg.cc/FKgJmjZW/08aabb32_724b_4f3e_b780_deb33d57119b.png)


# UISystem 代码结构​

新增界面代码路径​
`Assets/Scripts/HOT/UISystems​`

![飞书文档 - 图片](https://i.postimg.cc/6QLGwd0Y/199bd2c6_a5a3_46ef_bc0c_db5d1e37015f.jpg)



## Model 代码​
![飞书文档 - 图片](https://i.postimg.cc/0N8yYhY0/飞书文档_图片_1765246773.jpg)
- Data  是自定义类型的数据封装​
- Repository 是全局数据缓存管理​

### 继承 BaseData​

全局数据管理类需要​

![飞书文档 - 图片](https://i.postimg.cc/DzdbFqgC/b1c8570d_8d34_4d05_bc08_ccf419a275bf.png)



### 访问数据 DataRepository ​

通过GetData<T> 泛型方法访问数据​
![飞书文档 - 图片](https://i.postimg.cc/CKFxG9GN/飞书文档_图片_1765246779.png)
## View 代码​

是界面UGUI相关的处理，参考 UITeamSkillView_v2​
- 继承  Dialog 或 PopupWindow ​
- 继承 IView​
![飞书文档 - 图片](https://i.postimg.cc/cJM8ZQmB/77869af6_648a_42f4_9c09_f50c77d96821.png)


## ViewModel 代码​

是界面的业务逻辑代码，参考 UITeamSkillViewModel_v2​
它主要将界面的业务逻辑，全部封装在一个ViewModel对象中，​
- 继承 IViewModel 接口​
![飞书文档 - 图片](https://i.postimg.cc/N0gj6Z6D/飞书文档_图片_1765246787.png)

- 将业务逻辑集中在这个处理​

## Service 代码​


### 单例 继承IService​
![飞书文档 - 图片](https://i.postimg.cc/1z93GbGv/飞书文档_图片_1765246790.png)


### 请求网络数据​

主要用于与服务器的交互，请求网络数据，在数据修改时，触发事件​
![飞书文档 - 图片](https://i.postimg.cc/yNvYvnjc/飞书文档_图片_1765246792.png)
