---
title: EM UI结构
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---
# EM UI结构​
## 一.UI显示逻辑构架​
### 1.UI逻辑显示简介​
EM的UI系统，使用Unity的UGUI+C# MonoBehaviour脚本挂载的方式制作。​
先做好UGUI的prefab-》然后挂载Window及相关子类拓展脚本-》通过脚本设置好UI参数-》将Prefab放入UI逻辑栈中管理​
UI逻辑栈分多个渲染层级，每个层级又有多个子层级，所有显示管理都在PopupWindowManager中。​
### 2.主要逻辑代码结构​
(1) PopupWindowManager文件中包含了UI逻辑构架的主要代码。​
(2) PrefabPath，RefPrefabClassType 对prefab路径，Bar等进行管理的自定义Attribute。​
(3) Window及子类PopupWindow，Dialog，NativeWindow，UIPuzzleResultMapController等窗口管理类。在制作Prefab的UI时，将相关自定义脚本挂载在Prefab上，然后在脚本上设置UI参数。同时，该类族也有窗口常见操作的逻辑代码，如打开，关闭，隐藏等。​
(4) 外部调用显示UI窗口的示例如下：​
界面：PopupWindowManager.Instance.showPopupWindow<UIPuzzleResultMapController>()​
隐藏当前显示界面：PopupWindowManager.Instance.HidePopupWindow()​
### 3.PopupWindow窗口显示结构​
（1）PopupWindow有显示内容的prefab和显示UI上面Bar的prefab，这两个prefab分开的。​
（2）显示Popupwindow时，先加载具体弹窗的Prefab，然后Instance一个WindowTopBar的prefab，放在弹窗Prefab界面上，整个弹窗才显示完整。​
（3）PopupWindow是需要入栈的UI，每次显示新UI，将最新UI放在栈上层。隐藏，则弹出最上层栈的UI，并销毁。​
（4）SetTitle：设置最上方显示的Bar​
（5）OnPause，OnResume，OnClosed：隐藏，恢复，销毁时的回调函数​
（6）示意图，1：bar  2:Prefab显示内容​
​​​![飞书文档 - 图片](https://i.postimg.cc/XvDwBkM9/fei-shu-wen-dang-tu-pian-1764824949.png)
​
### 4.PopupWindowManager中显示逻辑结构构架​
（1）EM所有显示逻辑构架都在PopupWindowManager的中管理，所以该类非常重要。​
（2）渲染层级定义，分为主层级 和 次级层级；​
主层级gameObject.layer/canvas.sortingLayerName/canvas.sortingLayerID设定，次级层级用canvas.sortingOrder设定；​
层级越大，显示越靠前；​
主层级大的必定显示在主层级小的UI之上；​
主层级相等时，次层级更大的，显示在次层级小的UI之上；​
特效的层级，通过UIAnimator设置，且只设置sorderOrder（次层级）。​
（3）显示UI的主要接口​
showPopupWindow：显示入栈弹窗，其他所有显示函数都是调用改函数。改函数加载UI的Prefab，组装TitleBar成完整可显示的UI，并显示在界面上。同时，逻辑入栈。​
HidePopupWindow，PopToWindow：显示出栈弹窗，并销毁在需要显示的Prefab。​
## 二.PopupWindowManager重要的逻辑代码详细解析​
### 1.代码中渲染主层级定义​
```csharp
private const int GUIDE_LAYER = 30; 引导UI的主层级​
private const int TIPS_LAYER = 31; 提示UI的主层级​
private const int SPEAKER_LAYER = 31;广播UI的主层级​
private const int MAINUI_LAYER = 10; 入栈的主UI的主层级的最小层级​
//入栈UI的当前最大层级，11~31，只渲染最上面可见的入栈UI主层级​
//有新UI入栈，maxLayer都会加一，出栈，减一​
private int maxLayer = MAINUI_LAYER + 1;​c
```

注意：引导，Tips，广播都是只有一个主层级，且写死的；但是入栈UI主层级有多个，每个入栈UI都有一个主层级(layer)，每次入栈加一，出栈减一。​
### 2.入栈的UI的次级层级(sortingOrder)排序相关定义：​
```csharp
//有新的UI入栈，都会将maxSortLayer + SORT_LAYER_INC，出栈 -SORT_LAYER_INC​
//（不明白有何意义，或许是为了每个层级都划分清楚）​
private const int SORT_LAYER_INC = 30; ​
//入栈UI当前最上面那个UI的sortingLayer​
private int maxSortLayer = 0;​
```

### 3.主层级的对象​
```csharp
private GameObject tipsWindow = null; //提示window ​
private GameObject guideWindow = null;//引导window ​
private GameObject puzzleguideWindow = null;//解密引导window ​
private GameObject speakerWindow = null; //广播消息window ​
//需要入栈的UI的对象缓存，每个UI都有一个GameObject，显示UI入栈，弹出UI出栈​
public Stack<GameObject> windowsStack = new Stack<GameObject>();​
```

除了入栈的ui栈，其他四个层级都是写死的，并且只有一个UI对象。​
### 4.showPopupWindow显示入栈UI逻辑细节​
（1）接口定义public T showPopupWindow<T>(bool guide = true, int index = 0) where T : Window​
（2）先根据T获取PrefabPath属性，获得prefab路径，并实例化。​
（3）若是PopupWindow，则根据胚子的WindowTopBar，实例化一个Bar，添加到UI的Prefab上，并赋值相关数据。​
（4）隐藏旧最上层UI，执行旧最上层UI的OnPause回调。​
（5）将新UI的Prefab放在一个新建的Cavans（UIWindowRootCameraCanvas）下，设置主层级和次层级，入栈新UI，并更新渲染显示，将新UI显示。​
### 5.HidePopupWindow/PopToWindow弹出栈UI逻辑细节​
（1）获取栈顶UI，执行销毁UI回调，销毁UI。​
（2）主层级和次级层级回退。​
（3）若是需要回退到特定界面，需要一直循环，直到最上层界面是特定界面为止。​
### 6.Tips/Speaker等特定UI​
这些特定UI，和普通入栈UI相比，有一些特殊处理，但是逻辑基本一致。而且只有一个UI界面，不会有入栈，出栈操作，渲染层级也是写死不变的。​

---

```csharp
using DG.Tweening;
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public abstract class Window : MonoBehaviour
{
    public bool isBackButtonEnable = true;
    public bool isOnPopToRoot = false;
    public bool isFullScreenInPC = false;
    //顶部bar的类型
    public enum WindowTopBar
    {
        None,
        Resource,
        Title,
        effects,
        ActionTitle,
        ReportTitle,
        GuildTitle,
        ReadTopBarInfo,
        OnlyReturn,
    }

    [System.Serializable]
    public struct WindowTopBarInfo
    {
        [EnumAttirbute("返回按钮是否显示")]
        public bool ShowCloseBtn;
        [EnumAttirbute("title是否显示")]
        public bool ShowTitle;
        [EnumAttirbute("资源道具图标显示数量（从右往左依次显示，只有两个）")]
        public int ShowResourcesNum;
        [EnumAttirbute("详情按钮是否显示")]
        public bool ShowInfoBtn;
        [EnumAttirbute("资源道具ID列表")]
        public uint[] ShowResourceIds;
    }

    public enum CanvasType
    {
        Camera,
        Screen
    }

    public enum PopupAnimationType
    {
        None,
        popupZoom,    //弹出时放大回缩
        popupEnlarge, //弹出后缓慢放大
    }

    public enum CloseAnimationType
    {
        None,
        closeZoom,    //关闭时放大回缩
        closeRetract, //关闭时缩小
        Nothing       //放最后，无任何关闭特效
    }

    public enum BackgroundType
    {
        None,
        Mask,//仅黑色背景
        MaskCloseButton,//黑色背景+点击背景关闭按钮
        MaskAndCloseButton,//黑色背景+点击背景关闭按钮+有实体关闭按钮点击
        NoneCloseButton,//透明背景+点击背景关闭按钮
    }

    public enum OpenWindowPlaySoundType
    {
        None, //手动选择 不播放声音
        Default,//默认声音 全屏界面播放 PopWindow_normal  弹窗界面播放 Dialog_normal
        Dialog_normal,//普通窗口界面
        Dialog_pay,//付费窗口界面
        PopWindow_normal,//普通全屏界面
        PopWindow_pay,//付费全屏界面
        GiftPackWindow,//礼包界面
        IrregularWindow,//非规则窗口
        FestivalWindow,//节日全屏界面
        PopupTipsWindow,//弹出tip界面
    }

    public enum CloseWindowPlaySoundType
    {
        None, //手动选择 不播放声音
        Default,//默认声音 播放 CloseUI_1
    }

    [HideInInspector]
    public delegate void OnWindowClosed();
    public OnWindowClosed windowCloseListener;
    [HideInInspector]
    public delegate void OnWindowOpened();
    public OnWindowOpened windowOpenListener;
    public virtual PopupAnimationType PopupAnimType { get; set; }
    public virtual CloseAnimationType CloseAnimType { get; set; }
    public OpenWindowPlaySoundType openWindowPlaySoundType = OpenWindowPlaySoundType.Default;
    public CloseWindowPlaySoundType closeWindowPlaySoundType = CloseWindowPlaySoundType.Default;
    public bool isNeedResorePosition = false;
    protected bool isPause = false;
    /// <summary>
    /// 是否覆在MainUI上。dialog的情况一般是true。窗口的情况一般是false
    /// </summary>
    /// <returns></returns>
    public abstract bool IsOverlayMainUI();
    /// <summary>
    /// 是否不透明。影响被遮住的window、场景是否渲染问题
    /// </summary>
    /// <returns></returns>
    public abstract bool IsOpaque();
    public int sortLayer;
    public bool isClose = false;
    public Sequence closeAnimSequence = null;

    public virtual void SetWindowVisible(bool isVisible)
    {

    }

    public void CloseWindow()
    {
        CloseWindow(false, true);
    }

    public void CloseWindow(bool popToRoot)
    {
        CloseWindow(popToRoot, true);
    }

    public virtual void CloseWindow(bool popToRoot, bool isCheckGuide)
    {
        if (isClose)
        {
            return;
        }
        //if (PopupWindowManager.Instance.windowsStack.Count > 0)
        //{
        //    Debug.Log($"CloseWindowFrom:{gameObject?.name}===>CloseWindow:{PopupWindowManager.Instance.windowsStack.Peek()?.gameObject?.name}");
        //}
        /*ky if (PopupWindowManagerAOT.Instance.StackCount > 0)
        {
            if (PopupWindowManagerAOT.Instance.IsPeekWindowObj(this.gameObject))
            {
                isClose = true;
            }
        }
        else
        {
            return;
        }
        PopupWindowManagerAOT.Instance.HidePopupWindow(popToRoot, isCheckGuide);*/
    }

    public virtual void OnPause()
    {
        isPause = true;
    }

    public virtual void OnResume()
    {
        isPause = false;
    }

    public virtual void OnClosed()
    {
        //ky PopupWindowManagerAOT.Instance.OnWindowClosed(this);
    }

    public virtual void OnCloseAnimationComplete()
    {
        //ky PopupWindowManagerAOT.Instance.SetLayer(this.gameObject);
        if (closeAnimSequence != null)
        {
            closeAnimSequence.Kill(false);
            closeAnimSequence = null;
        }
    }

    public virtual bool CheckCanClose()
    {
        return true;
    }

    public virtual bool ExitOnLogin()
    {
        return true;
    }

    public virtual bool PopupToRootOnLogin()
    {
        return true;
    }

    public virtual void OnLogin() { }

    public virtual PopupAnimationType GetWindowPopupAnimationType()
    {
        //if (!PlayerData.Instance.IsOpenUI2())
        //{
        //    return PopupAnimationType.None;
        //}
        return PopupAnimType;
    }

    public virtual CloseAnimationType GetWindowCloseAnimationType()
    {
        //if (!PlayerData.Instance.IsOpenUI2())
        //{
        //    return CloseAnimationType.None;
        //}
        return CloseAnimType;
    }

    public virtual void UIPopupAnimationComplete() { }

    public virtual void SetResorePosition(bool need = true)
    {
        isNeedResorePosition = need;
    }

    /// <summary>
    /// 做最后的清理.
    /// </summary>
    protected virtual void DoDestroy()
    {
        windowCloseListener = null;
    }

    protected virtual void OnDestroy()
    {
        DoDestroy();
    }
}

public class PopupWindow : Window
{
    [HideInInspector]
    //ky public UIWindowTopBar titleBar = null;

    public WindowTopBar topBarType = WindowTopBar.Resource;
    [Header("ReadTopBarInfo类型数据")]
    public WindowTopBarInfo windowReadTopBarInfo;

    public string titleKey = "";
    public bool showBackBtnBg = true;
    public bool isOpaque = true;

    [HideInInspector]
    public delegate void OnWindowInfo();
    public OnWindowInfo windowInfoListener;

    //  public bool isCloseBtnShow=true;
    //是否覆盖显示在之前的window上。。窗口的情况一般是false
    public override bool IsOverlayMainUI()
    {
        return false;
    }

    public override bool IsOpaque()
    {
        return isOpaque;
    }

    public virtual WindowTopBar GetWindowTopBarType()
    {
        return topBarType;
    }

    /*ky public virtual string GetTitle()
    {
        return LocalizationManagerAOT.Instance.GetString(titleKey);
    }

    public void SetTitle(string title)
    {
        PopupWindowManagerAOT.Instance.SetTitle(titleBar, title);
    }

    /// <summary>
    /// 顶部info按钮点击事件
    /// </summary>
    /// <param name="clickListener"></param>
    public void SetInfoBtnCallBack(OnWindowInfo clickListener)
    {
        if (titleBar != null)
        {
            titleBar.reportButton.onClick.RemoveAllListeners();
            titleBar.reportButton.onClick.AddListener(delegate () { clickListener(); });
        }
    }*/
}

public class Dialog : Window
{
    public PopupAnimationType popupAnimType = PopupAnimationType.popupZoom;
    public CloseAnimationType closeAnimType = CloseAnimationType.closeZoom;

    public override PopupAnimationType PopupAnimType
    {
        get { return popupAnimType; }
        set { popupAnimType = value; }
    }

    public override CloseAnimationType CloseAnimType
    {
        get { return closeAnimType; }
        set { closeAnimType = value; }
    }

    public BackgroundType backgroundType = BackgroundType.None;
    public Button dialogCloseButton;

    public bool IsUseBlur = true;
    public override bool IsOverlayMainUI()
    {
        return true;
    }

    public override bool IsOpaque()
    {
        return false;
    }

    // 是否通过手动点击关闭窗口
    private bool _isCloseOnClick = false;
    public bool IsCloseOnClick
    {
        get { return _isCloseOnClick; }
        set { _isCloseOnClick = value; }
    }
}

public class NativeWindow : Window
{
    public override bool IsOverlayMainUI() { return true; }
    public override bool IsOpaque()
    {
        return false;//这里不能设置为true，否则插件窗口弹出时，游戏场景就隐藏了，会有闪动
    }
}

```

```csharp
using System;
using UnityEngine;

#if UNITY_EDITOR
using UnityEditor;
using System.Reflection;
using System.Text.RegularExpressions;
#endif

/// <summary>
/// 设置枚举名称
/// </summary>
#if UNITY_EDITOR
[AttributeUsage(AttributeTargets.Field)]
#endif
public class EnumAttirbute : PropertyAttribute
{
    /// <summary>
    /// 枚举名称
    /// </summary>
    public string name;
    public EnumAttirbute(string name)
    {
        this.name = name;
    }
}

#if UNITY_EDITOR
[CustomPropertyDrawer(typeof(EnumAttirbute))]
public class EnumNameDrawer : PropertyDrawer
{
    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        // 替换属性名称
        EnumAttirbute enumAttirbute = (EnumAttirbute)attribute;
        label.text = enumAttirbute.name;

        bool isElement = Regex.IsMatch(property.displayName, "Element \\d+");
        if (isElement)
        {
            label.text = property.displayName;
        }

        if (property.propertyType == SerializedPropertyType.Enum)
        {
            DrawEnum(position, property, label);
        }
        else
        {
            EditorGUI.PropertyField(position, property, label, true);
        }
    }

    /// <summary>
    /// 重新绘制枚举类型属性
    /// </summary>
    /// <param name="position"></param>
    /// <param name="property"></param>
    /// <param name="label"></param>
    private void DrawEnum(Rect position, SerializedProperty property, GUIContent label)
    {
        EditorGUI.BeginChangeCheck();
        Type type = fieldInfo.FieldType;

        string[] names = property.enumNames;
        string[] values = new string[names.Length];
        while (type.IsArray)
        {
            type = type.GetElementType();
        }

        for (int i = 0; i < names.Length; ++i)
        {
            FieldInfo info = type.GetField(names[i]);
            EnumAttirbute[] enumAttributes = (EnumAttirbute[])info.GetCustomAttributes(typeof(EnumAttirbute), false);
            values[i] = enumAttributes.Length == 0 ? names[i] : enumAttributes[0].name;
        }

        int index = EditorGUI.Popup(position, label.text, property.enumValueIndex, values);
        if (EditorGUI.EndChangeCheck() && index != -1)
        {
            property.enumValueIndex = index;
        }
    }
}
#endif

public class ChineseEnumTool : MonoBehaviour
{
}
```

