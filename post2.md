---
title: 通用UI组件文档与备注
category: 代码解析
date: 2025年12月03日
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 为了能够快速复用组件，请大伙尽量写的能够复用
tags: 美术,程序
---

为了能够快速复用组件，请大伙尽量写的能够复用  

PackageRes/LocalResource下面尽量不要修改，里面的prefab也不要引用子的prefab,最好全break掉（子的prefab容易被动修改后导致local里面的资源引用到外部资源），一定要用到本地的prefab修改的或者新建的，一定要注意里面所有的图片资源引用都必须引用local下的资源

主界面弹窗队列管理功能接口。以后在主界面自动弹出的活动弹窗请调用ViewUtil.RequestToMainQueue接口(弹窗优先级配置表_PopupPriorityConfigure.xlsx)。如果还有本地记录弹出时间的请在接口的回调里面保存，因为这个功能会限制单次登录主界面最大弹出数量，多出来的会被吞掉。

本地化存储使用：
LocalCache.GetGlobalXXX,GetLocalXXX, Local和账号绑定,GLobal和机器绑定

最好能做个base基类 这样 额外需求也好扩展 不然可能属性加的有点多
能做复用变体 就更好了
所有的text组件都不能使用系统自带的，使用工程中的EvonyText 这种

新手期间的界面和加载 大家在维护自己的代码的时候顺手把PopupWindowManager.Instance.showPopupWindow修改为PopupWindowManager.Instance.showPopupWindowAsync或者PopupWindowManager.Instance.showPopupWindowTask
把ExPrefab.LoadPrefab修改为ExPrefab.LoadPrefabAsync或者ExPrefab.LoadPrefabTask,后面的都是异步的写法，改成异步的就支持小包插队下载资源了

## 通用组件 存放位置

Assets\PackageRes\Raw\Category\Prefabs\UI\Cell
集合预制体 Assets\CommonPrefab\ViewPrefab 用来方便看 目前有哪些可用的组件 
必须的 指 一定要用该预设 如果有差异 请在群内讨论，然后找美术协商

### UI （基础预设）

- 玩家头像  UIBestTeamAvatarCell(必须)s
- 英雄头像 UIAvatarCel(必须)
- 称号 UIHeroTitleCell (必须)
- 藏品 CollectionBaseCell (预设 ，特殊可不用 可继承对应类扩写)
- 通用道具 UIBagItemCell （按需使用吧，永远跟不上美术的变化快）
- 上下滑动组件 CustomScrollRect （嵌套了些逻辑  这个按需使用吧）
- 排名奖励预览 UIBestTeamRewardCell（参考最强团队活动排名奖励预览 相似可拓展）
- 通用按钮 CommonBtn（按需使用）
- 通用物品数量的滑动条 UseAmount（按需使用）
- 通用升星组件 UIGeneralStarPanel28
- 通用英雄卡牌 UIGeneralCell
- 通用货币条 UIMoneyCell

### UI(变体预设)





## 特殊 

### 1. 下滑的多选项

- 别用unity自带的Dropdown   改为EvonyDropdown  不然下滑的多选项会在二级界面显示不出来  

### 2. scrollview中cell居中显示

- UIExtension.CenterItemAtIndex   scrollview中cell居中显示
- ScrollRect嵌套使用时，在将ScrollRect替换成CustomScrollRect使用，子父ScrollRect都需要替换

### 3. 科学计数法

- Int.HumanReadableByteCount(); 格式化显示科学计数法，例如：10M，6K

### 4. 关闭指定界面

- PopupWindowManager.Instance.CloseWindow<UITitleSuccessView>(gameObject); 关闭指定UI界面

### 5. 富文本字体颜色

- Text.text = “#000000”.GetRichTextFromTextColor(“文本内容”)；   //富文本字体颜色

### 6. 通过文本颜色获得Color

- Text.color = “#000000”.GetColor();  //通过文本颜色获得Color

### 7. 镜像图片

- 对称图片美术那边如果只出一半 添加mirror脚本即可

### 8. 震动效果

- DataChangeBroadcast.Instance.RaiseEvent(DataChangeType.NiceVibrations, 3);//震动效果

### 9. 表数据不对的可能解决方案

- C:\Users\Administrator\AppData\LocalLow\topgamesinc\Rg_alpha\configure 表数据缓存的路径，如果出现数据不对的情况下，可以尝试清理这个文件夹

### 10. Dropdown下滑时变多个内部组件颜色 

![飞书文档 - 图片](https://i.postimg.cc/G2rdMF4V/飞书文档_图片_1764828689.png)
- 比如这种修改 文字+颜色 ，将Dropdown的Template下Item的toggle替换为ToggleRG组件，结合 ToggleColorChange组件，可在对应 进入/放开/选中状态下 修改多个UI组件颜色

### 11. CoroutineRunner的协程使用方法. 

- CoroutineRunner.Start();不返回对象,由CoroutineRunner内部管理.协程执行完成后,自行入池,或者内部销毁
- CoroutineRunner.StartManual();返回对象,需要手动管理.常用模式:

```c#
if (cor != null) //使用前先保证清理.
{
	CoroutineRunner.Stop(cor);
}

cor = CoroutineRunner.StartManual(CheckAllConnectionResults());

//清理
if (cor != null) 
{
	CoroutineRunner.Stop(cor);
	cor = null;//置空,确保不重复stop.
}
```

### 12. LoadObjectProxy使用 

```c#
private LoadObjectProxy effectProxy;

private void OnDestroy()
{
	if (effectProxy != null)
	{
		LoadObjectProxy.Despawn(effectProxy);
		effectProxy = null;
	}
}

private Transform GetFXParent()
{
	throw new Exception("XXX");//
}

void InitProxy()
{
    if(effectProxy == null)
    {
        effectProxy = new LoadObjectProxy();
		effectProxy.Init(GetFXParent(),OnLoaded);
    }
}

private void OnLoaded(LoadObjectProxy proxy)
{
    if (this == null || fxParent == null)
    {
        CLog.Warning($"$OnLoaded:{this}:fxParent{fxParent}:target:{proxy?.Target}:{effectProxy == proxy}");
		proxy?.ClearResult();
		return;
    }
	if (effectProxy!=null && proxy == effectProxy)
	{
        if (effectProxy.Target != null)
        {
            InitQualityEffect(effectProxy.Target);
        }
    }
}
private void InitQualityEffect(Transform effectTarget)
{
    effectTarget.transform.localPosition = Vector3.zero;
	effectTarget.transform.localScale = Vector3.one;
	effectTarget.gameObject.PlayParticles();
}

```

### 13. PrefabHolder使用 

1. PrefabHolder挂GameObject上.
1. 将特效拖动到PrefabHolder,PrefabSource.
![飞书文档 - 图片](https://i.postimg.cc/vBMbPr1b/飞书文档_图片_1764828699.jpg)

### 14. UIParticle使用. 特效层级

UIParticle使用

### 15. RenderTextureCatcher使用

1. 创建的RenderTexture会安全的释放.
1. 确保内部的尺寸变化时候,能正常维护.

```c#
var catcher = rawImage.gameObject.GetOrAddComponent<RenderTextureCatcher>();
RectTransform tran = rawImage.rectTransform;
catcher.Catch((int)tran.rect.width, (int)tran.rect.height, RenderTextureFormat.ARGB32);
rawImage.texture = catcher.texture;
```

### 16. 常用开界面Utils封装.

1. MessageBoxUtils. Alert,单确认框.
1. ConfirmBoxUtils.封装UITwoButtonDialog.Confirm确认提示框.
1. TipsUtils.封装UIPopupTipsDialog,UIDetailWindow.
1. ViewUtils. 通用开界面接口

### 17. 顶部标题、资源显示及返回按钮

用到右下角返回按钮的界面都需要继承PopupWindow，根据需求设置当前界面显示的枚举
![飞书文档 - 图片](https://i.postimg.cc/501bPBHf/飞书文档_图片_1764828703.png)
1. 只显示标题和返回按钮选择：Titile，并再下面填入标题多语言Key
![飞书文档 - 图片](https://i.postimg.cc/PxhT6WLt/飞书文档_图片_1764828705.png)
1. 如果标题后需要跟着详情说明选择：ReportTitle，并在逻辑中调用
![飞书文档 - 图片](https://i.postimg.cc/fLZDHc3W/飞书文档_图片_1764828706.png)
1. 如果只需显示返回按钮选择：OnlyReturn
1. 如果顶部需要显示资源则需要在代码中设置相关资源显示
![飞书文档 - 图片](https://i.postimg.cc/vBzMC49y/飞书文档_图片_1764828707.png)
![飞书文档 - 图片](https://i.postimg.cc/G2Qr64Yr/飞书文档_图片_1764828708.png)

## 特权 (获取对应特权参数)

### 1. 战车副本系列门票 恢复次数

NewPrivilegeDataManager.DungenonTicketRecoveryTimesAdd(Msg.dungeon_type.对应战车副本类型)

### 2. 战车副本系列门票 上限

NewPrivilegeDataManager.DungenonTicketMaximumTimesAdd(Msg.dungeon_type.对应战车副本类型)

### 3. 免费挂机加速次数

NewPrivilegeDataManager.GetPrivilegeIntValue(PrivilegeRGType.OnHookFreeTimes)

### 4. 钻石挂机次数

NewPrivilegeDataManager.GetPrivilegeIntValue(PrivilegeRGType.OnHookGemTimes)

### 5. 挑战令上限

NewPrivilegeDataManager.GetPrivilegeIntValue(PrivilegeRGType.ChangellengTimes)

## 3D模型资源制作及导入unity相关技术流程

特效路径归类
RG项目：3D模型资源制作及导入unity相关技术流程
empty_85,empty_8 是全透明图片,可以用来防止第一次白图的.
每次setActive都会导致大量gc,本地已经有了数据信息,可以在start里面添加一次事件.

## 主界面活动图标优化-前端开发

## RG5.0红点系统使用文档.md

RG项目图文混排制作使用

