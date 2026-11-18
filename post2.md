---
title: 弹窗遮罩规范：CloseSelf 是默认，BlockOnly 要写明理由
category: "[代码解析]"
date: 2026-11-18
project: 猫骑士（Unity 小游戏）
---

猫骑士 155 个页面的遮罩行为登记在 `Migration/Input/modal-input.json`：CloseSelf 51 条、BlockOnly 25 条，例外都要附源码依据，442 条断言守着规范不被改坏。

## 一、规范只有一条：遮罩只允许两种行为

弹窗遮罩的一切行为收敛到一个 53 行的组件 `Assets/Root/Script/Core/Component/BlockInputEvents.cs`。它实现全套 EventSystem 接口（PointerDown/Up/Click、InitializePotentialDrag、Begin/Drag/EndDrag、Scroll），每个处理器都 `data.Use()` 把输入吞掉；行为分叉只有一个枚举：

```csharp
public enum ClickBehavior { CloseSelf, BlockOnly }

public void OnPointerClick(PointerEventData data)
{
    data.Use();
    if (!isActiveAndEnabled || !released || data.button != PointerEventData.InputButton.Left || pointer != data.pointerId) return;
    pointer = null;
    if (behavior == ClickBehavior.BlockOnly || owner == null || !owner.activeInHierarchy) return;
    if (closeButton != null)
    {
        if (closeButton.isActiveAndEnabled && closeButton.IsInteractable()) closeButton.onClick.Invoke();
    }
    else PopupMotion.Hide(owner);
}
```

两个细节是"吞得干净"的关键：按下/抬起配对（`pointer`/`released`），点在遮罩上滑出去再松手不会误关；`OnBeginDrag` 直接清空 `pointer`，拖拽手势不触发点击语义。

CloseSelf 的语义是**复用页面自己的关闭入口**：有关闭按钮就 `Invoke()` 它（走页面的取消回调和交互门槛），没有才 `PopupMotion.Hide(owner)` 只关自己。这保证了"点遮罩关闭"和"点取消按钮"走同一条业务路径，不会出现遮罩关了但回调没执行的分裂状态。

游戏里的「在线奖励」弹窗就是标准的 CloseSelf：遮罩把主城背景压暗，底部提示「点击空白处关闭」，点遮罩只关弹窗自己、不碰背后的主城页面：

![在线奖励弹窗：遮罩压暗背景，点击空白处按 CloseSelf 只关弹窗自己](images/post2-dialog-mask.png)

## 二、什么时候允许 BlockOnly：必须二选一的确认框

BlockOnly 只吞输入、不做任何关闭动作。典型场景是必须做决策的确认框——点遮罩等于替用户选了"取消"，这是产品事故。`Frames/Common/ConfirmationPage.cs` 把这条规则编码成了参数：

```csharp
public void Open(string heading, string message, Action<bool> callback, bool requireDecision = false)
{
    if (closed != null || callback == null) throw new InvalidOperationException("Open a confirmation once");
    title.text = heading; description.text = message; closed = callback;
    backdrop.SetBehavior(requireDecision ? BlockInputEvents.ClickBehavior.BlockOnly : BlockInputEvents.ClickBehavior.CloseSelf);
    confirm.onClick.AddListener(() => Finish(true)); cancel.onClick.AddListener(Cancel);
}
```

默认信息提示（requireDecision=false）点遮罩即关；`requireDecision: true` 时遮罩变 BlockOnly，用户只能在确认/取消里选一个。调用方必须**显式**传 true——目前全工程四处调用全部显式传参，没有一个靠默认值"碰巧"拿到 BlockOnly。兜底还有一层：`OnDisable` 时未结算的确认自动 `Cancel()`，弹窗被外部销毁不会留下悬空回调。

## 三、25 条例外，每条都有出处

行为分配不靠口头约定，登记在 `Migration/Input/modal-input.json`（2290 行）：

| 统计项 | 数量 |
| --- | --- |
| pages 总条目 | 155 |
| kind=modal（整页弹窗，behavior 必填） | 76 |
| kind=nonmodal（内嵌 prefab/道具，无整页遮罩） | 79 |
| behavior=CloseSelf | 51 |
| behavior=BlockOnly | 25 |

剩下 79 条 nonmodal 不是漏登记：它们是内嵌 prefab、道具、局部控件，没有整页遮罩所有权，条目里带 reason 说明（如 "embedded prefab/item; no full-page modal ownership"）。规范把"要不要管"也变成了显式决定——要么整页弹窗登记行为，要么明说"不归整页管"，没有第三种沉默状态。

每个 modal 条目的字段把"这个遮罩为什么这样"写死：`source` 指向 Laya 源场景/prefab，`mask` 是遮罩节点名，`close` 是复用的关闭按钮（可空），`bodies` 是要吞输入的弹窗主体，`backgrounds` 是要废掉 raycast 的旧遮罩；最关键的是 `evidence` 数组——每条 behavior 都附源码摘录（文件 + 掩码相关行），BlockOnly 的 25 条无一例外。工程约定（AGENTS.md）原话：BlockOnly 必须在 manifest 记录源依据。

也就是说，想给某个弹窗改成"点不关"，先在 manifest 里登记行为、理由和源码证据，再过检查——登记本身挡掉了大多数随手改。

## 四、规范怎么落进 prefab：作者工具，不是人肉

登记了 manifest 还得落到 86 个 prefab 上。`Assets/Editor/ModalInputMigration.cs` 是作者工具：按 manifest 在遮罩节点下建透明的 `__InputSurface` 子物体挂 BlockInputEvents，`Configure` 用 SerializedObject 写入 behavior/owner/closeButton：

```csharp
var surface = mask.transform.Find("__InputSurface")?.gameObject;
if (surface == null)
{
    surface = new GameObject("__InputSurface", typeof(RectTransform), typeof(Image)); surface.layer = 5;
    surface.transform.SetParent(mask.transform, false); Fill((RectTransform)surface.transform);
    surface.GetComponent<Image>().color = Color.clear;
}
Configure(surface, root, close, (string)row["behavior"] == "BlockOnly");
```

为什么是遮罩的**子物体**而不是遮罩本身？源码注释一句话讲清：`A child handler prevents legacy Buttons/EventTriggers on the mask or page from also receiving the gesture`——旧 Button 挂在遮罩上时，父节点先于子节点收到事件；反过来子物体处理完 `Use()` 掉，旧组件自然收不到。`bodies` 列表里的弹窗主体也补 BlockInputEvents（behavior 固定 BlockOnly）防点穿，旧 `backgrounds` 全部关掉 raycast——视觉保留、输入退场。

更硬的一道保险在保存时：`SavePrefab` 是所有页面作者的统一保存入口，保存前强制把 BlockInputEvents 的 `raycastTarget` 拉回 true、同层兄弟 Graphic 关掉——美术在编辑器里随手勾选 hit 标志，保存时会被自动纠正回登记过的状态。

## 五、检查：442 条断言 + 真实存档的运行时用例

规范有三层守卫：

- **资产层**：`ModalInputChecks.Authoring` 对 76 条 modal / 86 个 prefab 逐个校验，共 **442 条断言**，报告在 `Migration/Evidence/modal-input-assets.json`（2026-11-13，success=true）
- **运行时层**：`Tools/check-collected-loot.cjs --case modal-input` 在真实分包里跑 **49 条断言**（证据 `collected-loot-case-modal-input.json`），覆盖原生 raycast、down/up/click 配对、嵌套旧全屏 Button、信息型 vs 决策型确认、禁用/复用、daily-gift 输入 owner 清理
- **代码层**：manifest 的 codeHashes 固定包含 BlockInputEvents.cs、ConfirmationPage.cs、ModalInputMigration.cs、ModalInputChecks.cs——改这四个文件必须连 manifest 一起过检查

上线前核对：

- 新弹窗先在 `modal-input.json` 登记（source/behavior/evidence），再跑作者工具落 prefab
- 默认 CloseSelf；要 BlockOnly 先问"这个弹窗是否必须用户做决策"，理由写进 evidence
- 关闭永远复用页面关闭按钮（close 字段），禁止遮罩直连业务回调
- 美术改完 prefab 后重跑 `SavePrefab`（保存即纠正），再过 `check-modal-input.cjs`
- 改动 BlockInputEvents/ConfirmationPage 任何行为，同步更新 manifest 的 codeHashes 并跑全套 --case modal-input
