---
title: RG2.0版UI搭建流程及规范
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---

RG2.0版UI搭建流程及规范​


本文讨论了RG2.0版UI搭建流程及规范，涵盖基础规范、搭建流程规范、UI通用控件搭建和使用等方面。关键要点包括：​
1. 图片命名规范：只能含英文字母、数字、下划线，按「类型_名称_状态_序号」排列，类型有缩写，名称用英文或拼音，通用后缀固定，临时资源加xx_Temporary后缀，装饰和功能元素分开切图。​
1. 切图规范：无特殊纹理纯色图片输出为白色，有圆角贴边时留1px空白，长宽尺寸为偶数。​
1. 搭建流程规范：准备阶段对比需求和效果图，按命名规范切图，用工具对比重复；资源导入按尺寸和类型分目录；搭建阶段Prefab节点命名有规则，组件和功能角色有前缀；自测阶段检查图集依赖数量，除通用图集外不超3个。​
1. UI通用控件搭建和使用：模块化搭建先建基础组件，再建复合组件，用对应功能基础图片占位；搭建功能界面从预制体实例拼装，微调用Prefab Variant；搭建RG2.0版界面命名加“_v2”后缀。 ​

# 一.基础规范​


#### 图片命名规范​

基本原则​
1. 只能出现：英文字母、数字、下划线_，禁止空格​
1. 用下划线_做唯一分隔符，从左到右按「类型_名称_状态_序号」排列（bg属于使用场景，不作为前缀使用）​
- 第一段「类型」缩写​
| 缩写   | 含义                   | 举例                 |
|--------|------------------------|----------------------|
| btn    | 按钮（可点击）         | btn_buy_normal      |
| img    | 纯图片                 | img_dialog_bg       |
| txt    | 文字贴图（美术字）     | txt_num_kill        |
| icon   | 小图标                 | icon_skill_100001   |
| tab    | 标签页                 | tab_bottom_sel      |
| slider | 滑动条                 | slider_hero_hp      |
| input  | 输入框底板             | input_chat_bg       |
| toggle | 单选/复选              | toggle_display_on   |
| mask   | 遮罩                   | mask_circle         |

- 第二段「名称」​
用英文或拼音，保持简洁，避免英文和拼音混写的情况​
grayhead✔ huitouxiang✔ graytouxiang❌​
1. 通用后缀必须放在最后一段，且固定缩写：​
- _n —— 九宫格（九宫格切图）​
- _v —— 二方连续（纵向平铺）​
- _h —— 二方连续（横向平铺）​
- _t —— 四方连续​
示例：img_dlg_pattern_bg_h​
备注：​
- 拼接时如果部分图片资源是临时使用的（如活动顶部插图）或仅用于Prefab模板效果展示的，命名加上xx_Temporary后缀，该后缀资源不合入beta且定期清理​
- 切图时装饰性元素和功能性元素分开切图，可减少高相似度的大图资源（如下图）​
![飞书文档 - 图片](https://i.postimg.cc/br1gjGZq/飞书文档_图片_1765245430.png)


#### 切图规范​

- 无特殊纹理的纯色图片输出为白色（搭建时再进行着色，以提高复用率）​
- 有圆角贴着边缘时，切图边缘留出1px空白，避免出现锯齿​
- 切图长宽尺寸都保持为偶数，避免应用缩放时像素偏移和版像素模糊等问题出现​

# 二. 搭建流程规范​


#### 准备阶段：​

- 对比需求文档和UI效果图明确功能需求，确定UI界面布局、交互逻辑​
- 按照命名规范切图输出​
- 使用图片对比工具（无需安装，解压后直接使用）对比此次切图和项目资源中是否有重复，如有重复则不要再上传​
- 小图对比Assets\PackageRes\Raw\Function\UIAtlas目录​
![飞书文档 - 图片](https://i.postimg.cc/Y2FbFPbm/飞书文档_图片_1765245437.png)

- 大图对比Assets\PackageRes\Raw\Category\UISprite目录​
![飞书文档 - 图片](https://i.postimg.cc/qBKjKFj3/飞书文档_图片_1765245439.png)
小图资源对比出重复相同图片时：​
- 当项目中资源是在通用资源目录则直接使用Assets\PackageRes\Raw\Function\UIAtlas\Common​
- 当项目中资源不是通用资源，且和此次要搭建的UI不是同一系统功能时，则复制一个该资源到此次系统并修改命名（加序号或加系统名）功能对应的资源目录（以避免一个系统界面预制体依赖的图集太多）​

#### 资源导入阶段：​

- 图片尺寸≥512px的导入到Assets\PackageRes\Raw\Category\UISprite目录​
- 小图导入到Assets\PackageRes\Raw\Function\UIAtlas目录​
- 通用资源Assets\PackageRes\Raw\Function\UIAtlas\Common目录​
- 其他资源导入其UI系统对应的资源目录​

#### 搭建阶段：​

Prefab节点命名规则​
节点命名规则参照：​UI 开发流程​
| 规则 | 说明 | 违规示例 | 正确示例 |
| :--- | :--- | :--- | :--- |
| **必须采用 PascalCase + 下划线分级** | 一眼看出层级与功能 | `btnconfirm` | `Btn_Confirm` |
| **同功能节点后缀必须统一** | 全局搜索可批量替换 | `IconHP`、`HpImg`、`BloodSprite` | `Img_Blood` |

组件类型前缀​
bg和root同级，为纯图背景​
root（节点类型Empty）为功能最上层父节点，其他节点都放在Root下​
| 前缀     | 节点类型              | 说明与示例                                                                 |
| :------- | :-------------------- | :------------------------------------------------------------------------- |
| `img_`   | Image                 | 图片/精灵。用于显示图标、背景、装饰等。<br>示例: `img_Icon`, `img_Bg`, `img_PlayerPortrait` |
| `txt_`   | Text                  | 文本。用于所有文字显示。<br>示例: `txt_PlayerName`, `txt_Score`, `txt_Desc`              |
| `btn_`   | Button                | 按钮。本身是一个带有Button组件的节点，通常内部包含Img和Txt。<br>示例: `btn_Start`, `btn_Options`, `btn_Close` |
| `go_`    | GameObject（空对象）  | 分组/空节点。用于将多个节点组织在一起，本身没有渲染组件。<br>示例: `go_HealthBar`, `go_DialogGroup`, `go_ItemRewards` |
| `sld_`   | Slider                | 滑动条。如血量条、进度条、音量调节杆。<br>示例: `sld_Progress`, `sld_Volume`            |
| `tgl_`   | Toggle                | 开关/复选框。<br>示例: `tgl_Music`, `tgl_Fullscreen`                        |
| `srv_`   | ScrollRect            | 滚动视图。用于可滚动区域。<br>示例: `srv_ItemList`, `srv_Leaderboard`                 |
| `ipt_`   | Input                 | 输入框。<br>示例: `ipt_Name`, `ipt_Chat`                                   |
功能角色前缀 (标明节点在UI中的功能或角色),通常与组件类型前缀组合使用（也可单独使用）​
| 前缀     | 全称/含义        | 常见组合示例             | 说明                           |
|----------|------------------|--------------------------|--------------------------------|
| Bg_      | Background       | img_Bg<br>img_Bg_Dialog  | 背景。通常是一个Image。       |
| Icon_    | Icon             | img_Icon_Weapon<br>img_Icon_Coin | 图标。物品、货币、技能等图标。 |
| Item_    | Item             | go_Item_Slot<br>img_Item_Bg | 物品相关。常用于物品槽、列表项。 |
| List_    | List             | go_List_Inventory<br>scv_List_Shop<br>list_Attribute | 列表。列表的容器或项。 |
| Tab_     | Tab              | btn_Tab_Shop<br>go_Tab_Content | 标签页。标签按钮或标签内容区。 |
| Mask_    | Mask             | img_Mask_Avatar<br>go_Mask | 遮罩。用于实现头像圆形裁剪等效果。 |
| Effect_  | Effect           | img_Effect_Glow<br>anim_Effect_Sparkle | 特效。纯美术特效，非功能组件。 |
| Bar_     | Bar              | sld_Bar_Health<br>img_Bar_Exp | 条状物。血条、经验条等。 |
| Count_ / Num_ | Count/Number | txt_Count_Item<br>txt_Num_Gold | 数量/数字。用于显示数量的文本。 |
结构示例：​
![飞书文档 - 图片](https://i.postimg.cc/jqfZf1ZW/飞书文档_图片_1765245463.png)
#### 自测阶段（图集依赖数量检查）​

优化要求：​
一个界面预制体依赖的图集数量除了通用图集“Common”以外，最多不超过3个​
检测方法：打开面板依赖检测工具​
​RG2.0版UI搭建流程及规范​
​

![飞书文档 - 图片](https://i.postimg.cc/66ZYZPY2/飞书文档_图片_1765245471.png)

![飞书文档 - 图片](https://i.postimg.cc/y88mLpyC/f5e86cb7-61e5-4159-8c21-7e7aafe3aa81.png)

![飞书文档 - 图片](https://i.postimg.cc/ZYNVNQVw/飞书文档_图片_1765245477.png)

# 三. UI通用控件搭建和使用​


#### 模块化搭建流程​

- 建立基础组件(Base Components)：最小的、不可再分的UI单元。​
- 例如：一个特定风格的按钮、一个文本标签、一个图标图片、一个单选框、一个滑动条等。​


- 要求：功能单一，可配置​
- 建立复合组件/通用控件 (Composite Components / Common Controls)：由多个基础组件组合而成的、具有特定功能的模块。​
- 例如：一个带图标和数量的物品槽(ItemSlot)、一个角色信息卡(AvatarCard)、一个通用的弹窗(CommonDialog)、一个列表中的一行(ListCell)等。​
- 目标：达到“开箱即用”的水平，通过配置就能满足80%的使用场景。​
注：基础组件和复合组件图片对象用对应功能的基础图片占位（有必要时请UI协助提供空状态图片），不要空着或用白图（便于他人辨认识别）​
- 搭建“功能界面”​
- 从CommonControls和BaseComponents中拖拽预制体实例到画布(Canvas)上进行拼装。​
- 绝对不要在功能界面里直接创建原始Image/Text来重做一个按钮或物品栏。​
- 如果某个模块需要微调（如某个地方的物品栏不需要数量文字），使用Prefab Variant（预制体变体）。​

#### 使用Prefab Variant（预制体变体）​

案例：商店的物品槽有边框，而背包里的物品槽没有边框，但其他都一样​
- 错误做法：复制Prefab_Common_ItemSlot.prefab并重命名Prefab_Common_ItemSlot_NoFrame.prefab，然后删除边框。这样两者就断了联系。​
- 正确做法：​
- 右键点击原始预制体Prefab_Common_ItemSlot.prefab。​
- 选择 Create -> Prefab Variant。​
- 将新变体命名为Variant_ItemSlot_NoFrame.prefab。​
- 在场景中打开这个Variant，仅禁用或删除边框节点。​
- 优势：如果之后原始预制体的图标大小改了，变体也会自动更新（边框依然保持不存在）。​
示例：​
基础控件CommonBtn3​
![飞书文档 - 图片](https://i.postimg.cc/jqfZf1Zv/飞书文档_图片_1765245482.png)

CommonBtn3变体→CommonBtn3_w300​
一些特殊界面搭配，修改宽度为300​
![飞书文档 - 图片](https://i.postimg.cc/mZ989n88/飞书文档_图片_1765245485.png)
备注：搭建RG2.0版界面时，相同功能界面创建预制体变体或复制为新预制体时，命名统一加“_v2”后缀（图片同理）​

