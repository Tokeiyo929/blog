---
title: 美术资源规范：1612 条资源清单就是法律
category: "[代码解析]"
date: 2026-11-18
project: 猫骑士（Unity 小游戏）
---

猫骑士的美术规范不靠文档靠清单：`package-layout.json` 里 1612 条资源逐条登记路径和 SHA256，改任何一张图、挪任何一次位置都会撞上 Verify 的哈希校验。

## 一、清单先于资源存在

`Migration/Input/package-layout.json` 顶层写着 `format: "catknight-packages-v1"`，resources 数组是全工程资源的唯一账本：

| 类型 | 条目 |
| --- | --- |
| png | 1451 |
| jpg | 16 |
| json | 56 |
| mp3 / wav | 46 / 43 |
| 合计 | 1612 |

1612 条图片、音频、数据文件分属 **19 个 bundle**，另有 154 条 userInterfaces 单独登记 UI 场景。每条资源五个字段：`source`（源文件名）、`bundle`（归属包）、`path`（Unity 工程路径）、`previous`（迁移前的旧路径）、`sha256`（内容哈希）。`previous` 让每一次挪位置都可溯源，`sha256` 让每一次改内容都可察觉——规范从"请勿修改"变成"修改必留痕"。

## 二、导入规则：像素守恒

清单管"有哪些图"，`Assets/Editor/TextureImportMigration.cs` 管"图以什么状态进 Unity"。全部 1509 张图按同一组导入设置落地：

```csharp
importer.textureType = TextureImporterType.Sprite;
// ...
importer.npotScale = TextureImporterNPOTScale.None;
importer.wrapMode = TextureWrapMode.Clamp;
importer.textureCompression = TextureImporterCompression.Uncompressed;
importer.maxTextureSize = Math.Max(importer.maxTextureSize, RequiredSize(importer));
```

NPOT 缩放显式关掉、mipmap 关掉、基础压缩关掉、Sprite 用 Single + FullRect——源图的每一个像素原样保留（尺寸 1440×1174 就是 1440×1174），这也是后面纹理压缩选型里"90.8% 的 Sprite 不是 4 的倍数"的由来。`RequiredSize()` 用 `NextPowerOfTwo(max(width, height))` 抬高尺寸上限，上限 16384，超限直接抛异常。

校验同样硬：`Importer()` 先比 SHA256——

```csharp
if (!File.Exists(path) || Hash(path) != (string)row["sha256"])
    throw new InvalidDataException("Image bytes differ from original: " + path);
if (Path.GetFileName(path) != Path.GetFileName((string)row["source"]))
    throw new InvalidDataException("Image name differs from original: " + path);
```

字节变了抛异常，文件名和清单 source 不一致也抛异常。基线 1509 = 原始 1486 + 审批恢复的 23 张，恢复语句的审批原文（"恢复这 23 张历史原图，基线改为 1509"）硬编码在代码里——基线只增不减，且每一步增都有书面批准。`Verify()` 逐张比对 `texture.width/height` 与源图尺寸、GUID 唯一且不丢失，报告落在 `Migration/Evidence/texture-import.json`。

## 三、图集：13 个模块图集，边界写在代码里

SpriteAtlas 按 Frame 模块划分，13 个包各一个：`Assets/Frames/FrameXxx/Atlas/FrameXxx.spriteatlasv2`。哪些图进图集不是人工勾选，是 `FrameAtlasMigration.cs` 扫出来的：遍历全部 prefab，凡是被 `RawImage.texture`、`BitmapNumber.Digits` 引用、或被 `.mat` 材质依赖的纹理一律排除——

```csharp
// RawImage UV patches and material textures require the original texture coordinates.
foreach (var image in AssetDatabase.LoadAssetAtPath<GameObject>(path).GetComponentsInChildren<RawImage>(true))
    if (image.texture != null) unpacked.Add(AssetDatabase.GetAssetPath(image.texture));
```

排除理由就写在注释里：RawImage 直接用 UV 采样原图，打包会错位。图集自身的参数也锁死在代码里：`includeInBuild=false`（由分包管线接管）、`padding=4`、禁旋转禁紧排、`readable=false`、无 mip、Bilinear、sRGB、`maxTextureSize=2048`，任何一项漂移都会被下次同步改回来。

账本数字（`Migration/Evidence/frame-atlases.json`，2026-11-16）：13 个图集装了 **744 张 sprite、22 张打包纹理**；FrameCommon 最多（158 张），FrameMansion 最少（4 张）；被排除的 10 张 UV 图（back13.png 这类背景）保持独立。图集文件由 `PackageBuildMigration` 注册进对应 bundle（键 `atlas/<name>`），并且有一条跨包纪律：Frame 私有贴图被别的包引用直接抛异常——`move shared art to FrameCommon/Texture`，共享素材必须搬到公共包。本轮构建 bundleBytes 32,863,664，图集让包体增加了 732,404 字节，换来的是运行时 sprite 合批，而不是声称省显存。

## 四、字体：1825 个字符的子集

全工程只有一个字体：`Assets/Root/Texture/Font/CatKnightUI.otf`，825,628 字节——从 NotoSansCJKsc-Regular.otf（16,437,364 字节）子集化而来，只保留 **5%**。保留哪些字符由 `ci/common/tools/font-subset/characters.cjs` 收集：ASCII 可打印区 + 配置里的补充符号（货币、箭头、星级），再扫描 Assets 下全部 `.cs/.json/.prefab/.unity/.asset`，解码 `\uXXXX` 转义，共 739 个输入文件、1825 个字符。

字体目录本身也是约束：`Verify()` 检查 `AssetDatabase.FindAssets("t:Font")` 的结果必须全部位于 `Assets/Root/Texture/Font/`，别处不许出现字体。子集的一致性由三重 SHA256 把守（字体、许可证、源字体），断言 `allTextFontsReferenceSubset` 与 `hudLabelsWithNativeGeometry===5` 写在 `ci/tests/test-font-subset.cjs`——新增文案用了字集外的字符，检查会直接报 "Regenerate"。

## 五、压缩归档位，规范归清单

注意导入规范里 `textureCompression = Uncompressed`：GPU 压缩不在导入环节做，而是构建时由纹理档位（ASTC 4x4/6x6/8x8）统一决定，编辑器和 CI 共用一份档位表——细节见[纹理压缩选型：90.8% 的 Sprite 不是 4 的倍数，我们硬拒了 ETC2](post24.html)。导入保持像素原样、构建按档位压缩，两层各管一件事。

上线前核对：

- 新增资源先登记 `package-layout.json`（source/bundle/path/sha256），再放进 Assets；改图必须同步更新清单哈希
- 导入设置不许手工改：npotScale=None、mip off、Uncompressed、Single+FullRect 是基线，`Verify()` 逐张比对尺寸与 GUID
- 图集参数（padding=4、maxTextureSize=2048、includeInBuild=false）由 `FrameAtlasMigration` 同步，不手工调整
- Frame 私有贴图被外部引用时先搬到 `FrameCommon/Texture`，不允许跨包私有依赖
- 新文案先跑字体字符收集，字集外的字符要么进 `extraCharacters` 要么换写法；重生成后三重 SHA256 对账
