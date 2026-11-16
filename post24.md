---
title: 纹理压缩选型：90.8% 的 Sprite 不是 4 的倍数，我们硬拒了 ETC2
category: "[代码解析]"
date: 2026-11-16
project: 猫骑士（Unity 小游戏）
---

做猫骑士的 Unity WebGL 包时，CI 硬拒了 ETC2：1509 张图里 1370 张（90.8%）宽或高不是 4 的倍数，Unity 实测全部导成 RGBA32，4bpp 优惠落空。

## 一、一次 ETC2 全量导入实验：一行警告，九成图没压上

按"安卓保底用 ETC2"的惯性，这本该是个省事的决定。我们先跑了一遍全量导入，结果 Unity 只回了一行警告：

```
Only textures with width/height being multiple of 4 can be compressed to ETC2 format
```

然后把那批图实际导成了 RGBA32。证据留在 `Migration/Evidence/texture-compression-native.json`：只看 PNG 的子集里，1492 张有 1357 张（91.0%）命中这个限制；把 jpg 一起算上，1509 张待导入图里 1370 张（90.8%）宽或高不是 4 的倍数。

这笔账按源尺寸、RGBA32（4 字节/像素）算，1509 张图共约 216.4MB，其中不对齐的 1370 张占 187.4MB——86.6% 的纹理内存，恰好落在 ETC2 压不到的地方：

| 方案 | 按源尺寸计算的驻留 | 结论 |
| --- | --- | --- |
| RGBA32（不压缩） | 216.4MB | 现状基线 |
| ETC2 RGBA8（只有 139 张压得上） | 201.9MB | 省 14.5MB，约 6.7% |
| ETC2 RGB4（为了 4bpp 丢掉 Alpha） | 191.0MB | 省 25.3MB，但 UI 透明没了 |
| ASTC 4x4 | 54.1MB | 实测 Unity 导入存储 57.4MB |

这是按源尺寸的理论账，实际导入还会受 `maxTextureSize`、图集和加载策略影响；但它足以说明一件事：ETC2 在我们工程里不是"画质差一点"，而是**大部分图根本没压缩**。

顺带解释为什么不能直接拿 png/jpg 当显存纹理：它们压缩率高，但**不支持像素随机访问**。GPU 采样只读局部，png/jpg 却要按顺序解压整张图；它们适合磁盘和下载，不适合渲染时驻留。纹理压缩的本质是**固定大小的像素块 → 固定大小的字节块**，解码发生在每一次采样里，所以必须有损、定长、可随机访问。

## 二、这些尺寸是怎么活到导入阶段的

一般项目里，非 2 的幂次尺寸常在导入时被缩放掉，4 的倍数问题也就被顺手掩盖。我们恰恰相反：迁移到 Unity 时写了 `Assets/Editor/TextureImportMigration.cs`，把 1509 张图全部按 Sprite 导入，并显式关掉 NPOT 缩放、mipmap 和基础压缩，保留源图的每一个像素：

```csharp
importer.textureType = TextureImporterType.Sprite;
// ...
importer.npotScale = TextureImporterNPOTScale.None;
importer.wrapMode = TextureWrapMode.Clamp;
importer.textureCompression = TextureImporterCompression.Uncompressed;
importer.maxTextureSize = Math.Max(importer.maxTextureSize, RequiredSize(importer));
```

`RequiredSize()` 用 `NextPowerOfTwo(max(width, height))` 算尺寸上限，但不改图本身；`Verify()` 逐张比对 `texture.width/height` 与源图尺寸，并把 GUID、文件名和 SHA256 一起钉进基线。于是 1440×1174 的地图、650×1100 的副本图、807×799 的特效图都原样进了导入管线——1370 张不对齐的图，一共 578 种不同尺寸。

这不是为了难为压缩格式，而是迁移期的硬约束：Laya 时代的 Sprite 切片、锚点和 UI 布局都按原始像素对齐，批量 padding 会同时改图、改 meta、改图集，风险远大于收益。选压缩格式时，这个前提不能动。

## 三、候选格式过筛：ETC2 为什么出局

把移动端能选的格式按"能不能接住这 578 种尺寸"过一遍：

| 格式 | 分块方式 | 比特率 | Alpha | 在我们工程里的结论 |
| --- | --- | --- | --- | --- |
| ETC1 | 4×4 → 64bit | 4bpp | ✗ | UI 几乎全带透明，直接出局 |
| ETC2 | 4×4 → 64/128bit | RGB 4bpp / RGBA 8bpp | ✓ | 尺寸限制命中 90.8% 的图，实际回退 RGBA32，出局 |
| PVRTC | 非分块 | 2/4bpp | ✓ | 要求 POT，578 种尺寸要批量 padding，出局 |
| DXT/BC | 4×4 | 4~8bpp | 部分 | 桌面格式，WebGL 移动端不认，出局 |
| ASTC | 4×4~12×12 | 8bpp 到低于 1bpp | ✓ | 任意尺寸，唯一不需要改源图的选项 |

- **ETC1** 是 ES 2.0 的保底格式，但无 Alpha；我们大量 UI 图带透明，不能选。
- **ETC2** 补上了 Alpha，仍是"基色 + 偏移"的老思路，对渐变和色度变化大的块失真明显；更致命的是 4×4 块要求宽高都能被 4 整除，否则 Unity 回退 RGBA32。上面那次实验就是证据。
- **PVRTC** 是 PowerVR 时代的老格式，把纹理拆成低频颜色图和高频调制图，解码时放大混合；它要求 2 的幂次尺寸。为了一个格式去 padding 1370 张图，等于让美术管线为压缩格式让路。
- **DXT/BC** 只在桌面 Windows 上有意义，WebGL 小游戏不适用。

所以问题不是"ETC2 和 ASTC 哪个画质好"，而是"谁能不改一张源图就把这 1509 张图压进去"。ETC2 在第一关就输了。

## 四、ASTC：任意尺寸，质量与体积同时赢

ASTC 是 ARM 和 AMD 在 2012 年联合发布的格式，也是这一档里唯一不受专利约束的。它把分块压缩做成可调：块大小从 4×4 到 12×12，对应压缩比 3:1 到 27:1，比特率可以小数级调节（BISE 编码），支持 1~4 通道、LDR/HDR，并且**支持 NPOT 尺寸**——块在边缘补齐，源图尺寸不用动。这正是 578 种尺寸的解法。

质量与体积也不是二选一。UWA 给过一组 512×512、无 Alpha、开 Mipmap 的测试数据：

| 格式 | 体积 | 画质 |
| --- | --- | --- |
| RGB8 原图 | 1MB | 无损 |
| ETC2 4bit | 170.7KB | 明显失真 |
| ASTC 6x6 | 154.7KB | 无明显失真 |
| ASTC 8x8 | 85.4KB | 无明显失真 |

ASTC 6x6 比 ETC2 4bit 更小且更清晰；ASTC 8x8 体积只有 ETC2 的一半，画质仍然更高。对应到我们的 216.4MB 基线，三个档位的理论驻留分别是 54.1MB、24.0MB、13.5MB；档位 1 的实测导入存储是 57.4MB，与理论值同一量级（差异来自边缘补齐和导入细节）。

档位经验（结合 UWA 与 NVIDIA 的测试数据）：

- 无 Alpha 的普通贴图：ASTC 8x8 起步，角色面部、场景地面到 6x6
- 法线贴图对精度敏感：5x5 起步，要求高用 4x4
- 带 Alpha 的贴图压缩质量会下降：建议 5x5，特效和 UI 用 4x4
- 同一格式下有无 Alpha 不改变体积，只改变质量——Alpha 冗余时把 Alpha Source 设为 None，白拿一档质量

兼容性方面：iOS 从 A8（iPhone 6 / iPad mini 4）起全线支持；安卓从 OpenGL ES 3.1 起支持，UWA 2020 年统计覆盖率约 98.5%。安卓生态的默认选项也从 ETC2 逐步转向 ASTC。

## 五、把结论钉进 CI：一个白名单 + 一次事务

选型没有停在文档里。档位表放在 `settings/texture-compress.config.json`，编辑器和 CI 共用：

```json
{
  "schemaVersion": 1,
  "levels": {
    "0": { "format": "RGBA32", "maxTextureSize": 8192, "compressionQuality": 100 },
    "1": { "format": "ASTC_4x4", "maxTextureSize": 8192, "compressionQuality": 100 },
    "2": { "format": "ASTC_6x6", "maxTextureSize": 1024, "compressionQuality": 100 },
    "3": { "format": "ASTC_8x8", "maxTextureSize": 512, "compressionQuality": 100 }
  }
}
```

档位 1 是默认：ASTC 4x4，画质优先；档位 2/3 逐步降尺寸上限，体积优先，代价是 UI、字体、Spine 图集清晰度；档位 0 是 RGBA32 对照，专门用来排查画质问题。开关走 profile：顶层或 `common` 配 `textureLevel`，`platforms.<platform>.textureLevel` 可按渠道覆盖，改档只改一个值再构建。

拒绝 ETC2 不是文档约定，而是 `Assets/Editor/GameNexusTextureCompression.cs` 里 `Begin()` 的硬校验：

```csharp
if (!Enum.TryParse((string)settings["format"], out TextureImporterFormat format) ||
    !new[] { TextureImporterFormat.RGBA32,
        TextureImporterFormat.ASTC_4x4, TextureImporterFormat.ASTC_6x6, TextureImporterFormat.ASTC_8x8 }.Contains(format))
    throw new InvalidDataException("Uniform WebGL texture format must be RGBA32 or ASTC_4x4/6x6/8x8; ETC2 leaves non-block-aligned sprites uncompressed.");
```

异常消息就是选型理由。后来者想把格式改回 ETC2，会先撞上这堵墙——文档会被遗忘，抛异常不会。

应用发生在 AssetBundle 和播放器构建之前，整个构建包在一次压缩会话里（`ci/common/tools/unity-build/GameNexusBuild.cs`）：

```csharp
using (GameNexusTextureCompression.Begin(req.textureLevel, backup)) Run(req);
```

会话只改 WebGL 平台 override，源图和 Default 平台不动；`maxTextureSize` 取 min(档位上限, 原默认上限)；`crunchedCompression` 强制关闭；已经符合目标设置的纹理直接跳过，重复构建幂等。遍历范围是全工程 `Assets/` 下的 TextureImporter + SpriteAtlasImporter，图集和散图一视同仁。档位 1 的一次构建报告里，`textureCount=1542`、`atlasCount=13`、`changedCount=1555`。

还原按事务设计：先把所有将改动的 `.meta` 逐字节备份，再开始导入；报告写进 `texture-backup/texture-compression-report.json`，用原子写入（先写 `.tmp` 再 `File.Replace`，Windows 索引器短暂占用时退避重试 5 次）。进程被强杀时保留备份目录，用 Unity CLI 调 `GameNexusTextureCompression.Restore(@"<备份目录>")` 手动恢复，而不是用 Git 一把丢掉可能混入的用户改动。

验证脚本 `ci/tests/test-texture-compression.cjs` 覆盖了四个档位的实际格式与尺寸、异常还原、源图与 meta 哈希一致性；还故意让档位 3 的构建抛 `OperationCanceledException`，确认失败路径也能还原，且 `Restore()` 可重复调用。档位 3 的 512 上限会把 577×248 的 logo 缩成 512×220，这类尺寸变化也在用例里逐张断言。

## 六、代价与检查单

诚实说，ASTC 不是每台设备都认。WebGL 2 不保证 ASTC 扩展存在；不支持时 Unity 可能把纹理解压回 RGBA32，包体和画质都要真机验证。测试里 `SystemInfo.SupportsTextureFormat(ASTC_4x4)` 在编辑器的桌面 GPU 上返回 `false`，这正说明导入格式和运行时能否直接用是两件事。

上线前逐项核对：

- profile 里 `textureLevel` 明确声明，构建报告 `textureCompressionReport` 有 textureCount / changedCount
- 构建结束后 `texture-backup/` 已还原，`git status` 里没有 `.meta` 残留改动
- 真机验证：不支持 ASTC 扩展的设备是否回退解压，运行内存是否在红线内
- 用档位 2/3 时过一遍 UI、字体、Spine 图集清晰度
- 抽检压缩质量：带 Alpha 的 UI 图和无 Alpha 的场景图分开看
- 想改格式？先读 `Begin()` 那行异常消息，再数一遍每个 Sprite 的宽高是不是 4 的倍数

## 参考

- [ASTC 纹理压缩格式详解（知乎）](https://zhuanlan.zhihu.com/p/158740249)
- [你所需要了解的几种纹理压缩格式原理（UWATech）](https://github.com/netoearth/markdown/blob/master/%E4%BD%A0%E6%89%80%E9%9C%80%E8%A6%81%E4%BA%86%E8%A7%A3%E7%9A%84%E5%87%A0%E7%A7%8D%E7%BA%B9%E7%90%86%E5%8E%8B%E7%BC%A9%E6%A0%BC%E5%BC%8F%E5%8E%9F%E7%90%86%20-%20UWATech%E7%9A%84%E4%B8%AA%E4%BA%BA%E7%A9%BA%E9%97%B4%20-%20OSCHINA%20-%20%E4%B8%AD%E6%96%87%E5%BC%80%E6%BA%90%E6%8A%80%E6%9C%AF%E4%BA%A4%E6%B5%81%E7%A4%BE%E5%8C%BA.md)
- [Unity 导入图片尺寸大小和压缩格式的问题（CSDN）](https://blog.csdn.net/linxinfa/article/details/108827197)
- [Unity Texture Import 文档](https://docs.unity3d.com/Manual/class-TextureImporterOverride.html)
