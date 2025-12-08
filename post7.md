---
title: RG程序入职文档
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---




---

RG程序入职文档​
本文讨论了 RG 程序入职相关的一系列信息，涵盖软件安装、权限申请、游戏操作、代码规范等多方面内容。关键要点包括：​
1. 软件安装教程：提供了 Unity 2018.4.36f1 (64 - bit)和 Unity 2022.3.49f1 的详细安装教程。​
1. 网络地址信息：给出了 unity 连接 Cache Server 地址、内网地址、多个 SVN 地址、bamboo 发版打包地址和 App 下载地址。​
1. 权限申请流程：SVN、bamboo 查看发版权限等申请均通过公司流息流 -> 我的申请 -> 系统权限进行，且有分组权限管理规范和申请流程图。​
1. 游戏登录要点：登录账号在 RGClient\Src\trunk\client\rg\Launcher 文件夹，需在玩家服务器创建账号，关闭电脑防火墙。​
1. 代码规范要求：PlayerPrefs 保存按指定方法，尽量复用通用组件，音效使用有规定，字符串使用有相关优化文档。​
1. 协议相关说明：协议文件位置在 trunk\server\codeGen2\protobuf\csproto，协议事件报红可生成代码，新增协议需重新生成。​
1. 报销材料要求：每个报销材料包含从 Cursor 后台下载的发票、收据和带人名币额度的信用卡支付截图，4 月起发票必须是公司的。 ​


# 1.Unity 2022.3.49f1 详细安装教程​


unity连接Cache Server地址​
192.168.41.234​
上海这边CacheServer:172.16.54.206​

# 2.内网地址​

https://qdshare.topgamesinc.com/​

# 3.SVN申请 ​

SVN 地址 http://qdsvn.topgamesinc.com:8090/svn_qd/lm/Src/trunk​
SVN beta回合制地址 http://qdsvn.topgamesinc.com:8090/svn_qd/lm/Src/branches/beta/client/rg​
SVN beta赛马娘地址 http://qdsvn.topgamesinc.com:8090/svn_qd/lm/Src/branches/beta3.0/client/rg​
SVN bet1.0地址http://qdsvn.topgamesinc.com:8090/svn_qd/lm/Src/branches/beta1.0/client/rg​
SVN 国服beta地址 http://qdsvn.topgamesinc.com:8090/svn_qd/lm/Src/branches/betaCN​
SVN 国服微信beta地址 http://qdsvn.topgamesinc.com:8090/svn_qd/lm/Src/branches/releaseWXNew2​
svn 权限 rg_developer_client_level3​
公司流息流->我的申请->系统权限​
分组权限： ​RG项目组权限管理规范​
​申请流程图 申请流程图​
​

# 4.bamboo  发版打包地址​

http://bamboonew.ggdev.co/browse/LM​
申请：公司流息流->我的申请->系统权限​
申请一个查看发版的权限  链接 http://bamboonew.ggdev.co/browse/LM-RAAC ​

### App下载地址​

https://rgalpha.ucimg.co/android/index.html?rand=0.7167453065439702​

# 5.游戏登录账号​


## 1.RGClient\Src\trunk\client\rg\Launcher 这个是账号登录游戏的文件夹​

登录玩家账号 需要在玩家服务器创建一个账号，才能确保AB正常​





## 电脑防火墙需要关闭才能登录​
![飞书文档 - 图片](https://i.postimg.cc/25kGVwtV/飞书文档_图片_1765199997.jpg)

![飞书文档 - 图片](https://i.postimg.cc/DfrSMTZH/480X480.jpg)

# 6.IFix更新手机包调试​

IFIX更新​
热更补丁本地调试 AOTdll和hotdll放到files目录下即可​
![飞书文档 - 图片](https://i.postimg.cc/q7JwzLFC/飞书文档_图片_1765200000.jpg)

![飞书文档 - 图片](https://i.postimg.cc/cJxhrmzt/飞书文档_图片_1765200002.jpg)
![飞书文档 - 图片](https://i.postimg.cc/nV4XPJzw/7d288b9f_e09d_44de_8317_105007cbe92e.jpg)


# 7.手机包日志显示​
![飞书文档 - 图片](https://i.postimg.cc/9fLpT93F/飞书文档_图片_1765200005.jpg)

# 8.ui图集制作说明​




![飞书文档 - 图片](https://i.postimg.cc/y6mDbHdp/cf9a5d10_3556_4619_aa7d_7ce8650aac2c.jpg)

# 9.游戏文件夹说明​
![飞书文档 - 图片](https://i.postimg.cc/Xvs8F5MY/飞书文档_图片_1765200008.jpg)
Category文件夹是所有预制体和UI  会打AB​
Function 文件夹是美术文件夹 不打AB的​
UIAtlas 大图 不打图集​

# 10.AB分级下载的​

![飞书文档 - 图片](https://i.postimg.cc/mZYP5sDX/a6ee39a1_bf5f_44f3_88f9_612a906b0f6e.jpg)
![飞书文档 - 图片](https://i.postimg.cc/zfxjWhmR/飞书文档_图片_1765200010.jpg)


优先级从后往下​

# 11.GM地址​

RG GM使用说明​

# 12.本地打AB流程 unity切换安卓平台​


## 1.开始打AB  大概10分钟​
![飞书文档 - 图片](https://i.postimg.cc/Zqwc3Nkp/飞书文档_图片_1765200013.jpg)
## 2.打出来的AB是在这里：​

![飞书文档 - 图片](https://i.postimg.cc/VNKRMtyC/飞书文档_图片_1765200016.jpg)






## 3.把文件放在这个文件夹：​
![飞书文档 - 图片](https://i.postimg.cc/446YSgdB/deca92f7_6b71_4340_83c6_71015976df40.jpg)



## 4.勾选就可以走AB了​
![飞书文档 - 图片](https://i.postimg.cc/vm0z9nRr/飞书文档_图片_1765200022.jpg)

# 13.任务需求单​


## 1.飞书搜索飞书项目  ​



![飞书文档 - 图片](https://i.postimg.cc/TPt9mb8J/飞书文档_图片_1765200025.png)

## 2.做完之后请勾选​
![飞书文档 - 图片](https://i.postimg.cc/wxX1GpvQ/1126a4e0_2977_48b6_abe5_1b1d89fafe48.png)

# 14.代码规范​

代码编写规范​
PlayerPrefs 保存使用以下方法​
​LocalCache_UsageGuide.md​

### 1.FR2工具可查看当前资源引用数量 ​


### 2.按钮，tog,道具，底框通用组件等尽量做通用组件复用​

装备子物体：Category/Prefabs/UI/Cell/EquipmentItemCell​
技能子物体：Category/Prefabs/UI/Cell/SkillItemCell​
头像子物体：Category/Prefabs/UI/Cell/UIAvatarCell​
背包子物体：Category/Prefabs/UI/Cell/UIBagItemCell​
通用按钮：Category/Prefabs/UI/Common/CommonBtn​
通用资源条：Category/Prefabs/UI/Common/UIMoneyCell​

### 3.音效 ​

UICustomButton 按钮音效​


NotificationCenter.Instance.RaiseEvent(NotificationType.PlayCommonSound, SoundEffectType.main_ui_04);​

### 4.通用组件文档​

通用UI组件文档与备注​

### 5.字符串使用​


# 15.协议文件说明​

trunk\server\codeGen2\protobuf\csproto​
![飞书文档 - 图片](https://i.postimg.cc/YSd3gFcf/飞书文档_图片_1765200031.png)


# 16.等待服务器反信时的动画效果​

使用UILoadingView.ShowLoadingView()显示转圈效果，表示正在向服务器请求数据。在收到服务器反信后使用UILoadingView.ShowHideLoadingView()关闭转圈动画效果。​
![飞书文档 - 图片](https://i.postimg.cc/tgB5P60S/飞书文档_图片_1765200033.png)


# 17.协议事件生成​

协助路径在这里http://qdsvn.topgamesinc.com:8090/svn_qd/lm/Src/trunk/server/codeGen2/protobuf/csproto可查看对应协议内容​
如遇到协议事件在编辑器中报红的情况，可点击Custom-协议-事件生成功能生成代码。​
新增协议也需要重新生成代码​
![飞书文档 - 图片](https://i.postimg.cc/R0gRftrd/飞书文档_图片_1765200036.png)


### 


# 18.前端如何使用读取新创建的表？​

1.在rg\Assets\Scripts\Configure 添加表格代码，参考其他表格读取代码改写​
2.注意代码需要使用Partial关键字，把代码放在ConfigureManager类下使用​
3.类字段的名称需要严格按照字段命名规范命名，类字段名称不可和其他表中声明的字段重名​
4.表有AB（整表替换）的情况下，需要使用ABTestManager.Instance.GetABTestConfigFileName("表名")获取正确的表名。并创建表名缓存，防止重复加载表。​
5.在表中添加方法，获取表中的相关数据。在方法最前面记得先读取表，防止读到空表。​
![飞书文档 - 图片](https://i.postimg.cc/pdsZ8jN6/飞书文档_图片_1765200039.png)
# 19.RG查看AB工具​


## 20.使用补丁​




## 21.cursor使用 cursor沟通交流群​

给大家一个一个核对材料太浪费时间了，我把文档上传到了飞书空间里，大家自己去检查自己的材料，有缺失的自己补充进去，我统一下载给财务。​
要求：​
1. 每个报销材料包含3个文件，分别是从Cursor后台下载的发票、收据和带人名币额度的信用卡支付截图。​
1. 3月份财务给开了特例，允许发票title是个人的。4月份开始发票必须是公司的，否则不能报销(开错发票的可以尝试退款重新购买)。​
1. 这些票据是给财务用来报销的，要求非常严格，请大家按照要求提供资料。​
，对所有群成员可见​
https://os3tzyabw2.feishu.cn/drive/folder/GhhWfJQATl0QyOdIIrsctGjSnv0​

# 新人必读​

👀新人必读​
飞书单 策划会对应任务库开子单，提交SVN记录需要提交任务库编号对应功能，未严格按照记录提交记录SI​
![飞书文档 - 图片](https://i.postimg.cc/TwhccPGj/飞书文档_图片_1765200044.png)
完成请勾选对号 ，需要填预估WH，实际WH，排期，和新PP类型​

---
