---
title: 选型靠实测不靠惯性：一次全量导入实验把 ETC2 判了出局
category: "[代码解析]"
date: 2026-11-16
project: 猫骑士（Unity 小游戏）
---

做猫骑士的 Unity WebGL 包时，CI 硬拒了 ETC2：1509 张图里 1370 张（90.8%）宽或高不是 4 的倍数，Unity 实测全部导成 RGBA32，4bpp 优惠落空。

## 一、"安卓保底 ETC2"是惯性，不是决定

按"安卓保底用 ETC2"的经验，这本该是个省事的决定。全量导入跑完，Unity 只回一行警告：

```
Only textures with width/height being multiple of 4 can be compressed to ETC2 format
```

然后把那批图实际导成了 RGBA32。证据钉在 `Migration/Evidence/texture-compression-native.json`（`eac4633f` 随档位系统一起入库），开头的 90.8% 就是从这份报告里数出来的。

这笔账落到内存上更扎心。RGBA32 基线 216.4MB，不对齐的 1370 张占 187.4MB——86.6% 的纹理内存恰好压不上；ETC2 只能接住 139 张，省 14.5MB（6.7%）；硬丢 Alpha 的 RGB4 省 25.3MB，但 UI 透明没了；ASTC 4x4 理论驻留 54.1MB，实测导入 57.4MB。ETC2 在我们工程里不是"画质差一点"，是**大部分图根本没压缩**。

九成图不对齐的出处是 11-10 的迁移决定（`f7142c8e`）：Laya 时代的 Sprite 切片、锚点和 UI 布局都按原始像素对齐，批量 padding 会同时改图、改 meta、改图集，风险远大于收益。于是 `TextureImportMigration.cs` 显式关掉了所有会"顺手掩盖"问题的导入选项：

```csharp
importer.textureType = TextureImporterType.Sprite;
// ...
importer.npotScale = TextureImporterNPOTScale.None;
importer.wrapMode = TextureWrapMode.Clamp;
importer.textureCompression = TextureImporterCompression.Uncompressed;
importer.maxTextureSize = Math.Max(importer.maxTextureSize, RequiredSize(importer));
```

一般项目里非对齐尺寸在导入时就被 NPOT 缩放抹平，我们保住了源图的每一个像素——1440×1174 的地图、650×1100 的副本图都原样进了管线，578 种尺寸里 1370 张不对齐。选压缩格式时，这个前提不能动。

## 二、候选过筛：谁能不改一张源图

| 格式 | 分块 | 比特率 | Alpha | 结论 |
| --- | --- | --- | --- | --- |
| ETC1 | 4×4 | 4bpp | ✗ | UI 全带透明，出局 |
| ETC2 | 4×4 | RGB 4 / RGBA 8bpp | ✓ | 90.8% 命中尺寸限制，回退 RGBA32，出局 |
| PVRTC | 非分块 | 2/4bpp | ✓ | 要求 POT，578 种尺寸要批量 padding，出局 |
| DXT/BC | 4×4 | 4~8bpp | 部分 | 桌面格式，WebGL 移动端不认，出局 |
| ASTC | 4×4~12×12 | 8bpp 到 <1bpp | ✓ | 任意尺寸，唯一不用改源图的选项 |

ETC2 输得不冤：4×4 块要求宽高都能被 4 整除，否则 Unity 回退 RGBA32，对渐变和色度变化大的块失真也明显。PVRTC 要求 2 的幂次，为一个格式让美术管线批量 padding 1370 张图，等于本末倒置。ASTC 把分块做成可调（4×4 到 12×12，压缩比 3:1 到 27:1），块在边缘补齐、源图不用动，578 种尺寸全部能覆盖；UWA 的实测里 ASTC 6x6 比 ETC2 4bit 更小且更清晰（154.7KB vs 170.7KB），8x8 体积减半画质仍更高。档位经验：无 Alpha 贴图 8x8 起步、角色和地面 6x6，法线 5x5 到 4x4，带 Alpha 的 UI 和特效 4x4；同一格式下有无 Alpha 不改体积只改质量，Alpha 冗余时把 Alpha Source 设为 None 白拿一档。兼容性上 iOS 从 A8 起全线支持，安卓从 OpenGL ES 3.1 起（UWA 2020 年统计覆盖率约 98.5%）。

## 三、拒绝钉进 CI：异常消息就是选型理由

选型没有停在文档里。档位表放在 `settings/texture-compress.config.json`（编辑器和 CI 共用）：档位 1 是默认 ASTC 4x4 画质优先，档位 2/3 降到 ASTC 6x6/8x8 且 `maxTextureSize` 收到 1024/512，档位 0 是 RGBA32 对照；profile 里一个 `textureLevel` 值可按渠道覆盖。真正拦住 ETC2 的是 `GameNexusTextureCompression.Begin()` 的硬校验：

```csharp
if (!Enum.TryParse((string)settings["format"], out TextureImporterFormat format) ||
    !new[] { TextureImporterFormat.RGBA32,
        TextureImporterFormat.ASTC_4x4, TextureImporterFormat.ASTC_6x6, TextureImporterFormat.ASTC_8x8 }.Contains(format))
    throw new InvalidDataException("Uniform WebGL texture format must be RGBA32 or ASTC_4x4/6x6/8x8; ETC2 leaves non-block-aligned sprites uncompressed.");
```

后来者想把格式改回 ETC2，先被 `throw` 拦下来。文档会被遗忘，抛异常不会。整个会话按事务设计：`.meta` 逐字节备份、报告原子写入、进程强杀后用 CLI `Restore()` 手动恢复；`ci/tests/test-texture-compression.cjs` 覆盖四档实际格式、异常还原和源图哈希一致性，连失败路径都故意触发过一次。

代价照实说：WebGL 2 不保证 ASTC 扩展存在，桌面编辑器上 `SupportsTextureFormat(ASTC_4x4)` 甚至返回 false。导入格式和运行时可用是两件事，真机回退和内存红线必须实测。

这套结论和官方文档的说法对得上。Unity 官方文档写明 "For Apple devices that use the A8 chip (2014) or above, ASTC is the recommended texture format"；安卓侧 ASTC 覆盖 ES 3.1/Vulkan 的现代 GPU（官方清单最早到 Mali T624，2012），ETC2 的定位则是 "If you need support for older devices" 的保底；官方同样确认不支持 ASTC 的设备会把纹理 "decompressed into an uncompressed RGBA 32-bit format"——正是我们那行警告看到的回退。官方文档都这么写，我们做的只是把 90.8% 的实测结果落成了 CI 硬校验。

回头看，这次没发明任何新东西，我们做对的只有两件：先跑全量实验拿到 90.8%，再让异常消息替文档守门。

## 参考

- [Unity 手册：GPU texture compression formats](https://docs.unity.com/en-us/engine/current/manual/materials-and-shaders/textures/textures-getting-started/texture-compression-formats)：ASTC 为 A8+ 与 ES3.1+ 设备的推荐格式，ETC2 为老设备保底
- [ASTC 纹理压缩格式详解（知乎）](https://zhuanlan.zhihu.com/p/158740249)
- [你所需要了解的几种纹理压缩格式原理（UWA）](https://github.com/netoearth/markdown/blob/master/%E4%BD%A0%E6%89%80%E9%9C%80%E8%A6%81%E4%BA%86%E8%A7%A3%E7%9A%84%E5%87%A0%E7%A7%8D%E7%BA%B9%E7%90%86%E5%8E%8B%E7%BC%A9%E6%A0%BC%E5%BC%8F%E5%8E%9F%E7%90%86%20-%20UWATech%E7%9A%84%E4%B8%AA%E4%BA%BA%E7%A9%BA%E9%97%B4%20-%20OSCHINA%20-%20%E4%B8%AD%E6%96%87%E5%BC%80%E6%BA%90%E6%8A%80%E6%9C%AF%E4%BA%A4%E6%B5%81%E7%A4%BE%E5%8C%BA.md)
