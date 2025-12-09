---
title: 红点系统使用文档
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---

## 📋 目录

- [系统介绍](#系统介绍)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [架构设计](#架构设计)
- [使用指南](#使用指南)
  - [UI组件使用](#ui组件使用)
  - [注册器实现](#注册器实现)
  - [动态红点注册](#动态红点注册)
  - [批量刷新](#批量刷新)
- [API文档](#api文档)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 🎯 系统介绍

红点系统是一个统一、高效、可扩展的游戏内通知提示系统。通过树形结构管理红点节点，支持静态预注册和动态运行时注册，提供灵活的刷新机制和批量操作能力。

### 设计目标

- ✅ **模块化设计** - 每个系统独立管理自己的红点逻辑，避免代码冲突
- ✅ **预注册机制** - 父节点可以在子界面未打开时识别到子界面的红点状态
- ✅ **动态扩展** - 支持运行时动态注册和注销红点节点
- ✅ **批量操作** - 支持批量标记脏数据和批量刷新，提升性能
- ✅ **类型安全** - 基于枚举类型，避免字符串拼写错误

---

## ✨ 核心特性

### 1. 模块化注册机制
- 每个系统通过实现 `IRedDotRegistrar` 接口独立管理自己的红点
- 自动发现和注册所有模块，无需配置文件
- 支持模块优先级控制

### 2. 预注册支持
- 游戏启动时预注册所有红点节点和处理器
- 父节点可以在子界面未打开时正确显示红点状态
- 避免硬编码的父子关系管理

### 3. 动态红点支持
- 支持运行时动态注册/注销红点节点（如新获得的英雄）
- 支持多入口红点（一个节点可以属于多个父节点）
- 支持实体实例红点（英雄ID、任务ID等）

### 4. 智能刷新机制
- 支持单个红点刷新
- 支持批量标记脏数据并选择性刷新
- 支持按类型或父节点批量刷新
- 自动向上冒泡聚合父节点状态

### 5. 生命周期管理
- 自动处理切号/重登场景
- 统一的事件订阅/退订机制
- 内存安全，避免泄漏

---

## 🚀 快速开始

### 1. 初始化红点系统

在游戏启动时初始化：

```csharp
RedDotManager.Instance.Init();
```

### 2. 在UI上挂载红点组件
已实现预制体`RedDotComponent.prefab`：

### 3. 创建注册器

```csharp
public class MySystemRedDotRegistrar : IRedDotRegistrar
{
    public RedDotDefine ModuleName => RedDotDefine.MySystemRoot;

    public void RegisterRedDots(RedDotRegistry registry)
    {
        // 注册静态红点树结构
        registry.RegisterNode(RedDotDefine.MySystemRoot, RedDotDefine.None);
        registry.RegisterNode(RedDotDefine.MySystem_SubPanel, RedDotDefine.MySystemRoot);
        
        // 注册处理器
        registry.RegisterHandler(RedDotDefine.MySystem_SubPanel, node =>
        {
            node.isActive = CheckMySystemCondition();
            node.count = node.isActive ? 1 : 0;
        });
    }

    public void OnStart(RedDotRegistry registry)
    {
        // 订阅事件，处理动态红点
    }

    public void OnStop(RedDotRegistry registry)
    {
        // 取消订阅事件
    }
}
```

---

## 🏗️ 架构设计

### 核心组件

```
RedDotManager (单例)
    ├── RedDotRegistry (注册表)
    │   ├── nodeRegistry (节点信息)
    │   ├── childrenRegistry (父子关系)
    │   └── handlerRegistry (处理器)
    └── IRedDotRegistrar[] (各模块注册器)
        ├── RegisterRedDots() (静态树注册)
        ├── OnStart() (订阅事件+动态注册)
        └── OnStop() (退订事件)

RedDotComponent (UI组件)
    └── 自动响应红点状态变化
```

### 数据流

```
数据变更事件
    ↓
Registrar 订阅的事件回调
    ↓
调用 RedDotManager.RefreshRedDot()
    ↓
RedDotRegistry 刷新节点状态
    ↓
向上冒泡刷新父节点
    ↓
广播状态变化事件
    ↓
RedDotComponent 自动更新UI
```

---

## 📖 使用指南

### UI组件使用

#### 基础使用

1. **在Prefab上挂载组件**
   - 在Inspector中选择要显示的红点类型（支持分类选择器）
   - 配置ID（如果是动态ID，保持枚举None，在实例化时通过代码设置）
   - 系统会自动响应红点状态变化

2. **代码动态设置**
   ```csharp
   var redDot = GetComponent<RedDotComponent>();
   
   // 静态红点
   redDot.RedDotKey = RedDotKey.Of(RedDotDefine.MainViewRoot);
   
   // 动态红点（如英雄卡片）
   redDot.RedDotKey = RedDotKey.Of(RedDotDefine.Hero_CardUpgradeable, heroId);
   ```

#### Inspector配置

- **分类选择器**：按下划线自动分组，选择分类后再选择具体类型
- **无下划线的枚举**：直接在一级下拉中选择，无需二级选择
- **ID输入框**：用于实体实例红点（如英雄ID、任务ID等）

### 注册器实现

#### 静态红点树注册

在 `RegisterRedDots()` 中注册静态的红点树结构：

```csharp
public void RegisterRedDots(RedDotRegistry registry)
{
    // 注册红点树结构
    registry.RegisterNode(RedDotDefine.HeroRoot, RedDotDefine.None);
    registry.RegisterNode(RedDotDefine.Hero_AnyUpgradeable, RedDotDefine.HeroRoot);
    registry.RegisterNode(RedDotDefine.Hero_AnyNew, RedDotDefine.HeroRoot);
    
    // 注册处理器
    registry.RegisterHandler(RedDotDefine.Hero_AnyUpgradeable, node =>
    {
        node.isActive = HasAnyHeroCanUpgrade();
        node.count = GetUpgradeableHeroCount();
    });
}
```

#### 动态红点注册

在 `OnStart()` 中订阅事件，处理动态红点：

```csharp
public void OnStart(RedDotRegistry registry)
{
    // 订阅英雄获得事件
    PlayerData.OnHeroAdded += heroId =>
    {
        var parentKey = RedDotKey.Of(RedDotDefine.Hero_AnyUpgradeable);
        var childKey = RedDotKey.Of(RedDotDefine.Hero_CardUpgradeable, heroId);
        
        // 注册节点
        registry.RegisterNode(childKey, parentKey);
        
        // 注册处理器
        registry.RegisterHandler(childKey, node =>
        {
            node.isActive = CanHeroUpgrade(heroId);
            node.count = node.isActive ? 1 : 0;
        });
        
        // 刷新红点
        RedDotManager.Instance.RefreshRedDot(childKey);
    };
    
    // 订阅英雄删除事件
    PlayerData.OnHeroRemoved += heroId =>
    {
        var childKey = RedDotKey.Of(RedDotDefine.Hero_CardUpgradeable, heroId);
        registry.UnregisterNode(childKey);
    };
    
    // 订阅数据变更事件
    PlayerData.OnHeroDataChanged += heroId =>
    {
        var childKey = RedDotKey.Of(RedDotDefine.Hero_CardUpgradeable, heroId);
        RedDotManager.Instance.RefreshRedDot(childKey);
    };
}

public void OnStop(RedDotRegistry registry)
{
    // 取消订阅所有事件
    PlayerData.OnHeroAdded -= ...;
    PlayerData.OnHeroRemoved -= ...;
    PlayerData.OnHeroDataChanged -= ...;
}
```

#### 多入口红点

支持一个节点属于多个父节点：

```csharp
// 任务红点同时属于主界面和任务界面
var taskKey = RedDotKey.Of(RedDotDefine.Task_Daily);
var parents = new RedDotKey[]
{
    RedDotKey.Of(RedDotDefine.MainViewRoot),
    RedDotKey.Of(RedDotDefine.TaskPanel)
};
registry.RegisterNodeWithMultipleParents(taskKey, parents);
```

### 动态红点注册

#### 运行时注册新英雄红点

```csharp
public void OnGetNewHero(int heroId)
{
    var parentKey = RedDotKey.Of(RedDotDefine.Hero_AnyUpgradeable);
    var childKey = RedDotKey.Of(RedDotDefine.Hero_CardUpgradeable, heroId);
    
    // 注册节点
    registry.RegisterNode(childKey, parentKey);
    
    // 注册处理器
    registry.RegisterHandler(childKey, node =>
    {
        node.isActive = CanHeroUpgrade(heroId);
        node.count = node.isActive ? 1 : 0;
    });
    
    // 刷新红点
    RedDotManager.Instance.RefreshRedDot(childKey);
}
```

### 批量刷新

#### 场景：获得升级材料后刷新所有英雄红点

```csharp
public void OnGetUpgradeMaterial()
{
    // 方案1：按父节点标记所有子节点为脏
    var parentKey = RedDotKey.Of(RedDotDefine.Hero_AnyUpgradeable);
    var allDirtyNodes = RedDotManager.Instance.MarkChildrenAsDirty(parentKey);
    
    // 方案2：按类型标记所有实例节点为脏（更精确）
    var heroCardNodes = RedDotManager.Instance.MarkSameTypeAsDirty(RedDotDefine.Hero_CardUpgradeable);
    
    // 根据业务需求决定刷新哪些节点
    // 例如：只刷新当前界面可见的英雄，避免不必要的计算
    var visibleHeroIds = GetVisibleHeroIds();
    var nodesToRefresh = heroCardNodes
        .Where(node => visibleHeroIds.Contains(node.id1))
        .ToList();
    
    // 批量刷新
    if (nodesToRefresh.Count > 0)
    {
        RedDotManager.Instance.RefreshRedDots(nodesToRefresh);
    }
}
```

#### 标记脏数据的方法

1. **`MarkChildrenAsDirty(RedDotKey parentKey)`**
   - 将指定节点下的所有子节点（递归）设置为脏
   - 适用于需要刷新某个父节点下的所有子节点

2. **`MarkSameTypeAsDirty(RedDotDefine type)`**
   - 将指定类型的所有节点（类型相同但ID不同）设置为脏
   - 适用于需要刷新同一类型的所有实例节点

---

## 📚 API文档

### RedDotManager

#### 初始化方法

```csharp
// 初始化红点系统（首次启动时调用）
void Init()

// 清理红点系统（Reloading时调用）
void Cleanup()
```

#### 查询方法

```csharp
// 检查红点数据是否可用
bool CheckRedDotDataIsAvailable(RedDotKey redDotKey)

// 获取红点状态
bool GetRedDotStatus(RedDotKey redDotKey)
```

#### 刷新方法

```csharp
// 刷新指定红点状态
void RefreshRedDot(RedDotKey redDotKey)

// 批量刷新红点状态
void RefreshRedDots(List<RedDotKey> redDotKeys)
```

#### 批量标记方法

```csharp
// 将指定节点下的所有子节点设置为脏
List<RedDotKey> MarkChildrenAsDirty(RedDotKey parentKey)

// 将指定类型的所有节点设置为脏
List<RedDotKey> MarkSameTypeAsDirty(RedDotDefine type)
```

### RedDotComponent

#### 属性

```csharp
// 红点键值（可在Inspector或代码中设置）
RedDotKey RedDotKey { get; set; }
```

#### 方法

```csharp
// 刷新红点显示状态
void RefreshRedDotStatus()

// 显示红点
void Show()

// 隐藏红点
void Hide()

// 隐藏红点数量文字
void HideText()
```

### RedDotRegistry

#### 注册方法

```csharp
// 注册节点（单个父节点）
void RegisterNode(RedDotKey nodeName, RedDotKey parentName)
void RegisterNode(RedDotDefine nodeName, RedDotDefine parentName)

// 注册节点（多个父节点）
void RegisterNodeWithMultipleParents(RedDotKey nodeName, RedDotKey[] parentNames)

// 注册处理器
void RegisterHandler(RedDotKey nodeName, Action<RedDotNodeInfo> handler)
void RegisterHandler(RedDotDefine nodeName, Action<RedDotNodeInfo> handler)
```

#### 注销方法

```csharp
// 注销节点
void UnregisterNode(RedDotKey nodeName)
void UnregisterNode(RedDotDefine nodeName)

// 注销处理器
void UnregisterHandler(RedDotKey nodeName)
void UnregisterHandler(RedDotDefine nodeName)
```

### RedDotKey

#### 创建方法

```csharp
// 创建静态红点键值（无ID）
RedDotKey.Of(RedDotDefine type)

// 创建实例红点键值（有ID）
RedDotKey.Of(RedDotDefine type, int id1, int id2 = 0)
```

#### 属性

```csharp
RedDotDefine type;  // 红点类型
int id1;           // 主ID（如英雄ID）
int id2;           // 可选ID（如槽位、天数等）
```

---

## 💡 最佳实践

### 1. 模块化开发

✅ **推荐**：每个系统实现自己的 `IRedDotRegistrar`
```csharp
public class HeroRedDotRegistrar : IRedDotRegistrar { ... }
public class TaskRedDotRegistrar : IRedDotRegistrar { ... }
```

❌ **不推荐**：把所有红点逻辑写在一个地方
```csharp
// 避免这样做
public class AllRedDotRegistrar : IRedDotRegistrar { ... } // 包含了所有系统的逻辑
```

### 2. 事件订阅位置

✅ **推荐**：在 `OnStart()` 中统一订阅事件
```csharp
public void OnStart(RedDotRegistry registry)
{
    PlayerData.OnHeroAdded += OnHeroAdded;
    PlayerData.OnHeroDataChanged += OnHeroDataChanged;
}

public void OnStop(RedDotRegistry registry)
{
    PlayerData.OnHeroAdded -= OnHeroAdded;
    PlayerData.OnHeroDataChanged -= OnHeroDataChanged;
}
```

❌ **不推荐**：在业务代码中散落订阅
```csharp
// 避免在UI代码中直接订阅
public class UIHeroPanel : MonoBehaviour
{
    void Start()
    {
        PlayerData.OnHeroAdded += ...; // 不要这样做
    }
}
```

### 3. 批量刷新优化

✅ **推荐**：先标记脏数据，再选择性刷新
```csharp
// 标记所有为脏
var dirtyNodes = RedDotManager.Instance.MarkSameTypeAsDirty(RedDotDefine.Hero_CardUpgradeable);

// 只刷新可见的
var visibleNodes = dirtyNodes.Where(node => IsVisible(node.id1)).ToList();
RedDotManager.Instance.RefreshRedDots(visibleNodes);
```

❌ **不推荐**：无差别刷新所有节点
```csharp
// 避免这样做
foreach (var hero in allHeroes)
{
    RedDotManager.Instance.RefreshRedDot(...); // 会刷新不可见的节点，浪费性能
}
```

### 4. 红点处理器逻辑

✅ **推荐**：处理器逻辑简单高效
```csharp
registry.RegisterHandler(RedDotDefine.Hero_Upgradeable, node =>
{
    // 简单快速的逻辑
    node.isActive = CanUpgrade();
    node.count = node.isActive ? 1 : 0;
});
```

❌ **不推荐**：在处理器中执行耗时操作
```csharp
registry.RegisterHandler(RedDotDefine.Hero_Upgradeable, node =>
{
    // 避免耗时操作
    LoadHeroDataFromServer(); // 不要这样做
    ComplexCalculation();     // 避免复杂计算
});
```

### 5. 命名规范

✅ **推荐**：清晰的枚举命名
```csharp
HeroRoot                    // 英雄系统根节点
Hero_AnyUpgradeable        // 英雄任意可升级
Hero_CardUpgradeable       // 英雄卡片可升级
Hero_CardUpgradeable_1     // 英雄1的卡片可升级
```

❌ **不推荐**：模糊的命名
```csharp
Hero1          // 不清楚是什么意思
HeroRed        // 太模糊
Hero_Red       // 不够具体
```

---

## ❓ 常见问题

### Q1: 如何支持多入口红点？

A: 使用 `RegisterNodeWithMultipleParents()` 方法：

```csharp
var nodeKey = RedDotKey.Of(RedDotDefine.Task_Daily);
var parents = new RedDotKey[]
{
    RedDotKey.Of(RedDotDefine.MainViewRoot),
    RedDotKey.Of(RedDotDefine.TaskPanel)
};
registry.RegisterNodeWithMultipleParents(nodeKey, parents);
```

### Q2: 如何实现动态红点（如新获得的英雄）？

A: 在 `OnStart()` 中订阅事件，在回调中注册节点：

```csharp
public void OnStart(RedDotRegistry registry)
{
    PlayerData.OnHeroAdded += heroId =>
    {
        var childKey = RedDotKey.Of(RedDotDefine.Hero_CardUpgradeable, heroId);
        registry.RegisterNode(childKey, parentKey);
        registry.RegisterHandler(childKey, node => { ... });
        RedDotManager.Instance.RefreshRedDot(childKey);
    };
}
```

### Q3: 获得材料后如何刷新所有英雄红点？

A: 使用批量标记方法：

```csharp
// 标记所有英雄卡片为脏
var dirtyNodes = RedDotManager.Instance.MarkSameTypeAsDirty(RedDotDefine.Hero_CardUpgradeable);

// 只刷新可见的英雄
var visibleNodes = dirtyNodes.Where(node => IsVisible(node.id1)).ToList();
RedDotManager.Instance.RefreshRedDots(visibleNodes);
```

### Q4: 如何确保父节点在子界面未打开时也能显示红点？

A: 在 `RegisterRedDots()` 中预注册所有节点和处理器，系统会自动计算父节点状态。

### Q5: 切号时红点系统如何处理？

A: 系统已自动处理：
- `Reloading()` 时调用 `RedDotManager.Instance.Cleanup()` - 清理所有数据
- 登录成功后系统会自动重新初始化 - 重建所有红点树

### Q6: 如何调试红点系统？

A: 使用以下方法：
```csharp
// 检查红点数据是否可用
bool isAvailable = RedDotManager.Instance.CheckRedDotDataIsAvailable(key);

// 获取红点状态
bool isActive = RedDotManager.Instance.GetRedDotStatus(key);

// 手动刷新
RedDotManager.Instance.RefreshRedDot(key);
```

---

## 📝 更新日志

### v1.0.0 (当前版本)

- ✅ 模块化注册机制
- ✅ 预注册支持
- ✅ 动态红点注册
- ✅ 批量刷新机制
- ✅ 多入口红点支持
- ✅ 生命周期管理

---

## 🤝 贡献指南

1. 遵循现有的代码风格和命名规范
2. 每个系统独立实现自己的 `IRedDotRegistrar`
3. 在 `OnStart()` 中统一管理事件订阅
4. 使用批量刷新优化性能
5. 添加适当的注释和文档

---

## 📞 技术支持

如有问题或建议，请联系红点系统维护团队。

