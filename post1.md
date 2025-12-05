---
title: PrefabHolder
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---

# prefab中特效的处理方式

本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。关键要点包括：​
1. 特效处理方式：使用 PrefabHolder 动态加载特效 prefab，用 SortingGroup 控制 prefab 层级（UIParticle 自带层级无需处理），特效偏移和缩放记录在挂 prefab 的 transform 节点，复杂情况需程序监控 PrefabHolder 加载完成事件处理，层级复杂时使用 UIParticle。​

1. 基于 UIParticle 的特效处理：UIParticle 需要设置 Scale，虽未实现但给出了具体步骤示例。​

1. 特效处理步骤：选中特效定位位置，右键解包，清理除 SortingGroup 外的脚本并删除特效下节点，添加 Prefab 节点并将特效 prefab 拖入 PrefabHolder，预览特效，保存前确保特效不在显示树，最后进入游戏检测。​

1. 特效未加载：检查 AutoLoad 是否被选中，点击检测按钮检测对象是否存在。​

1. 特效缩放不对：注意资源本身 transform 坐标、旋转和 scale，PrefabHolder 上的位置和旋转是特效加载后的位置和旋转值。​

1. 特效位置不对：同特效缩放问题，注意资源本身 transform 坐标、旋转和 scale 以及 PrefabHolder 上的位置和旋转。​

1. 层级不对：添加 UIParticle 则调整自然层级，非 UIParticle 需在节点添加 SortingGroup 并用 ChildCanvas 调整其值。 ​

  

## 解决问题：​

1. 特效嵌入prefab，导致资源卸载困难​

1. 特效嵌入prefab，导致纹理资源冗余​

1. 制作方式统一​

1. 最大程度减少程序接入​
​

## 一. 处理方式：​

1. 使用PrefabHolder动态加载特效prefab​
1. 使用SortingGroup控制prefab的层级.(UIParticle自带层级,不用处理)​
1. 特效偏移和缩放记录在挂prefab的transform节点.​
1. 复杂情况,需要程序监控PrefabHolder的加载完成事件处理.​
1. 在层级复杂到SortGroup无法处理,使用UIParticle​

## 二. 基于UIParticle的特效处理​

未实现. UIParticle需要设置 Scale.

具体步骤.
举例:
prefab:UIGeneralStarPanel28
特效:fx_star_up
说明: 当前文件只有节点引用,所有不用添加任何代码.
![飞书文档 - 图片](https://i.postimg.cc/9McVMgMw/飞书文档_图片_1764824948.jpg)

1. 选中fx_star_up.点select,定位到fx_star_up特效在项目中的位置.
![飞书文档 - 图片](https://i.postimg.cc/pTkvnQhY/飞书文档_图片_1764824953.jpg)
1. 点击fx_star_up,右键->Prefab->unPack.​

![飞书文档 - 图片](https://i.postimg.cc/rmgTtG0N/飞书文档_图片_1764824955.png)
1. 清理fx_star_up上的除了SortingGroup的其他脚本.并删除特效下节点.​

![飞书文档 - 图片](https://i.postimg.cc/0QZvJGMS/飞书文档_图片_1764824957.jpg)
1. 添加Prefab节点.并将特效prefab拖入到PrefabHolder的prefab栏.
![飞书文档 - 图片](https://i.postimg.cc/C1J0fCBD/飞书文档_图片_1764824959.jpg)
1. 预览特效.点击预览,可以查看特效在prefab中的表现. 这里主要只能调整包括SortingGroup,和节点的位置和缩放.​


![飞书文档 - 图片](https://i.postimg.cc/JnK8B3D6/飞书文档_图片_1764824960.jpg)
1. 保存. 保存前,先清理下确保特效不在显示树上.​

![飞书文档 - 图片](https://i.postimg.cc/V64wb9r4/飞书文档_图片_1764824962.jpg)

1. 进入游戏检测.​
## 注意事项:
1. 特效未加载.​
检查AutoLoad是否被选中.点击检测按钮,检测对象是否存在.​
1. 特效缩放不对​
注意资源本身transform坐标 旋转和scale。PrefabHolder上的位置和选择,是特效加载后的位置和旋转值​
1. 特效位置不对​
注意资源本身transform坐标 旋转和scale。PrefabHolder上的位置和选择,是特效加载后的位置和旋转值​
1. 层级不对​
如果特效添加了UIParticle.那么调整自然层级.就可以了​
如果非UIParticle,需要在节点上添加SortingGroup,然后使用ChildCanvas来调整SortingGroup的值.​

---

```c#
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Events;
using Object = UnityEngine.Object;

/// <summary>
/// 目的:解除Prefab之间的直接依赖.
/// 支持加载Prefabs目录下的资源.
/// </summary>
public class PrefabHolder : MonoBehaviour
{
    /// <summary>
    /// 加载路径.
    /// </summary>

    private LoadObjectProxy proxy;
    [SerializeField] private Vector3 localPosition;
    [SerializeField] private Quaternion rotation;
    [HideInInspector][SerializeField] private string PrefabSource;
    [HideInInspector][SerializeField] private bool AutoLoad = true;

    public String Source => PrefabSource;
    public Transform Target => proxy != null ? proxy.Target : null;

    private bool isLoaded = false;

    /// <summary>
    /// OnDestroy会自动清理事件监听.
    /// </summary>
    //ky public UnityEvent<string, GameObject> CompleteEvent = new PrefabLoadCompleteEvent();
    private void Start()
    {
#if UNITY_WEBGL || WEIXINMINIGAME
        return;
#endif
        if (!string.IsNullOrEmpty(PrefabSource) && AutoLoad)
        {
            InitObjectProxy();
            proxy.Load(string.Empty, PrefabSource);
        }
    }

    protected virtual Transform GetParent()
    {
        return this.transform;
    }

    private void InitObjectProxy()
    {
        if (proxy == null)
        {
            //ky proxy = LoadObjectProxy.Spawn();
            proxy.Init(GetParent(), OnLoadObj, null, null);
        }
    }

    /// <summary>
    /// 
    /// </summary>
    /// <param name="source"></param>
    /// <param name="isAutoLoad"></param>
    /// <param name="loadedAction"></param>
    public void SetSource(string source)
    {
        InitObjectProxy();
        /*ky
        if (proxy.IsResultTarget(string.Empty, source))
        {
            return;
        }*/

        proxy.Load(string.Empty, source);
    }

    public bool IsLoaded()
    {
        return isLoaded;
    }

    public void Load()
    {
#if UNITY_WEBGL || WEIXINMINIGAME
        return;
#endif
        if (isLoaded || AutoLoad)
        {
            return;
        }
        if (!string.IsNullOrEmpty(PrefabSource))
        {
            InitObjectProxy();
            proxy.Load(string.Empty, PrefabSource);
        }
    }


    public void InitData(string source, bool isAutoLoad = false, Vector3 position = default, Quaternion rotation = default)
    {
        this.PrefabSource = source;
        this.AutoLoad = isAutoLoad;
        this.localPosition = position;
        this.rotation = rotation;
    }

    private void OnLoadedComplete(string PrefabSource, Transform target)
    {
        try
        {
            //ky CompleteEvent.Invoke(PrefabSource, target?.gameObject);
        }
        catch (Exception e)
        {
            //ky CLog.Error(e.ToString());
        }
    }

    private void OnLoadObj(LoadObjectProxy obj)
    {
        if (obj == proxy)
        {
            //ky CLog.Log(SysLogType.Res, $"ResLoaded:{PrefabSource},Target:{obj.Target}");
            if (obj.Target != null)
            {
                obj.Target.localPosition = localPosition;
                obj.Target.rotation = rotation;
                if (transform != null)
                {
                    SetLayer(obj.Target.gameObject, transform.gameObject.layer, true);
                }
            }
            OnLoadedComplete(PrefabSource, obj.Target);
            isLoaded = true;
        }
    }

    private void OnDestroy()
    {
        if (proxy != null)
        {
            LoadObjectProxy.Despawn(proxy);
            proxy = null;
        }

        //ky CompleteEvent?.RemoveAllListeners();
    }

    private static void SetLayer(UnityEngine.GameObject gObject, int layer, bool includeChildren = false)
    {
        if (gObject == null)
        {
            return;
        }
        gObject.layer = layer;
        if (includeChildren)
        {
            foreach (Transform child in gObject.transform)
            {
                SetLayer(child.gameObject, layer, true);
            }
        }
    }
}
```


