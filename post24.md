---
title: 纹理压缩选型：为什么我们的小游戏用 ASTC 而不是 ETC2
category: "[代码解析]"
date: 2026-11-16
project: 猫骑士（Unity 小游戏）
---

## 一、为什么 GPU 不吃 png 和 jpg

做移动端游戏绕不开纹理压缩。一笔账就能看清：未经压缩的 RGBA32 一个像素 4 字节，一张 512×512 的图就是 1MB，2048×2048 直接 16MB——这还只是一张贴图。内存之外还有**带宽**：渲染 3D 场景时大量贴图要经总线传给 GPU，带宽是发热的元凶，不限制的话手机秒变暖手宝。

那 png、jpg 压缩率不也很高吗？问题是它们**不支持像素随机访问**。GPU 渲染时只采样需要的部分，而 png/jpg 想读某个像素得按顺序解压整张图——这对 GPU 完全不可用。它们适合做下载传输和磁盘存储，不适合做渲染时驻留显存的纹理。

所以纹理压缩的本质是一套固定规则：**固定大小的像素块 → 编码进固定大小的字节块**，有损、固定速率。编码慢无所谓（打包时跑一次），解码必须快到不拖渲染——因为它发生在每一次采样里。在 Unity 中，jpg/png 只是源文件，导入后转成 Texture2D，真正进包的是按目标平台转换后的压缩纹理。

## 二、移动平台的几大压缩格式

| 格式 | 分块方式 | 比特率 | Alpha | 典型平台 | 一句话原理 |
| --- | --- | --- | --- | --- | --- |
| ETC1 | 4×4 → 64bit | 4bpp | ✗ | 所有 OpenGL ES 2.0 安卓机 | 每块两个基色，像素按 2bit 选择器在基色修饰值中取色 |
| ETC2 | 4×4 | RGB 4bpp / RGBA 8bpp | ✓ | OpenGL ES 3.0+ | 兼容 ETC1，质量略高，但色度变化大的块误差更大 |
| PVRTC | 非分块 | 2/4bpp | ✓ | PowerVR（苹果老设备） | 低频 A/B 图双线性放大后与全分辨率调制图 M 混合，必须 POT |
| DXT/BC | 4×4 | 4~8bpp | 部分 | 桌面 Windows | 块截断编码：两个基色 + 每像素插值索引，BC7 才追上 ASTC 质量 |
| ASTC | 4×4~12×12 | 8bpp 到低于 1bpp | ✓ | ES 3.0+ / iOS A8+ / 桌面 | 固定 128bit 块，块内像素数可变，按内容自适应选择压缩模式 |

几个关键差异值得展开：

**ETC 系**是安卓的"保底"格式——ETC1 受所有 ES 2.0 GPU 支持，但它不支持 Alpha；要透明通道得上 ETC2 的 RGBA 8bit，比特率翻倍到 8bpp。ETC2 的编码还是"基色 + 偏移"的老思路，对渐变和色度变化剧烈的图失真明显。

**PVRTC** 是苹果设备的老格式，思路和分块压缩完全不同：整张纹理拆成低频信号（两张缩小 4 倍的颜色图）和高频信号（记录混合权重的调制图），解码时放大再混合。它要求 POT（2 的幂次方）尺寸，如今在 ASTC 面前已无优势。

**ASTC** 是 2012 年由 ARM 和 AMD 联合发布的格式，也是唯一不受专利约束的一档。它把分块压缩玩出了花：块大小从 4×4 到 12×12 可选，对应的压缩比从 3:1 到 27:1，比特率可以小数级调节（BISE 编码）；支持 1~4 通道、LDR/HDR，而且**支持 NPOT 尺寸**。压缩算法会为变化更大的通道自动分配更高权重，单色图用很低的比特率就能有很好的效果。

顺带说下 POT 这件事：Unity 默认会把导入的图片尺寸转成 2 的 N 次方（比如 640×1138 变成 512×1024），这是图形硬件分块存储的偏好决定的。虽然 ES 3.0 之后 API 层面支持 NPOT，但 2 的幂次方纹理依然更优——制作资源时尽量按实际使用尺寸对齐，避免高精度压缩到低精度使用。

## 三、ASTC 的账本：质量与体积同时赢

UWA 那篇 ASTC 详解给过一组直观的测试数据。同一张 512×512、不带 Alpha、开 Mipmap 的贴图：

| 格式 | 体积 | 画质 |
| --- | --- | --- |
| RGB8 原图 | 1MB | 无损 |
| ETC2 4bit | 170.7KB | 明显失真 |
| ASTC 6x6 | 154.7KB | 无明显失真 |
| ASTC 8x8 | 85.4KB | 无明显失真 |

ASTC 6x6 比 ETC2 4bit **更小且更清晰**；ASTC 8x8 体积只有 ETC2 的一半，画质仍然更高。这不是"用质量换体积"的取舍，而是全面占优。

选档经验（结合 UWA 与 NVIDIA 的测试数据）：

- 无 Alpha 的普通贴图：ASTC 8x8 起步就够，要求高的（角色面部、场景地面）到 6x6
- 法线贴图对精度敏感：5x5 起步，要求高用 4x4
- 带 Alpha 的贴图压缩质量会明显下降：建议 5x5，特效、UI 这类要求高的用 4x4
- 同一格式下有无 Alpha 不改变体积，只改变质量——如果 Alpha 通道是冗余的，把 Alpha Source 设为 None 就能白拿一档质量

兼容性方面：iOS 从 A8 处理器（iPhone 6 / iPad mini 4）起全线支持；安卓从 OpenGL ES 3.1 起支持，2020 年 UWA 统计市面覆盖率就已有约 98.5%。安卓生态的默认选项这些年正是从 ETC2 逐步转向 ASTC。

## 四、我们的选择：拒绝 ETC2 的那个决定性理由

我们是 Unity WebGL 出微信/抖音小游戏包。按"安卓保底"的惯性思维，ETC2 似乎理所应当——但我们最终在 CI 里把选型**统一为 ASTC，并且直接在代码里拒绝了 ETC2**。

决定性原因是工程事实：**本工程大量 Sprite 的宽高不是 4 的倍数**。ETC2 是 4×4 块格式，Unity 在 WebGL 下处理这类非块对齐纹理时会将其**实际导入为 RGBA32**——也就是说完全不压缩。ETC2 的 4bpp 优惠在我们项目里大面积落空，包体和运行内存一点没省，还带着"已经选了压缩格式"的心理安慰。

ASTC 虽然也是块压缩，但支持任意尺寸：不用改源图、不用批量 padding、不用重切 Sprite，选它意味着美术资源和图集管线零改动。

次要原因是一致性：一套档位可以同时覆盖 TextureImporter 和 SpriteAtlasImporter 的 WebGL override，自动化、验证、回滚都只需要一条路径。

代价也要诚实说：WebGL 2 不保证设备支持 ASTC 扩展，不支持时 Unity 可能回退解压成 RGBA32，内存和画质的表现必须真机验证。这是我们的遗留观察项，见文末检查单。

## 五、CI 实现：一个档位 + 一次事务

选型结论没有留在文档里，而是固化成了代码。整套机制由三部分组成：档位配置、构建接收器、事务性还原。

### 档位表

档位定义在 `settings/texture-compress.config.json`，编辑器和 CI 共用一份：

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

- 档位 **1**（默认）：ASTC 4x4，保留原默认导入尺寸上限，画质优先
- 档位 **2**：ASTC 6x6 + 尺寸上限 1024；档位 **3**：ASTC 8x8 + 上限 512，体积优先，但可能伤 UI/字体/Spine 图集清晰度
- 档位 **0** 是 RGBA32 不压缩，专门留给排查画质问题时做对照

开关走 profile：顶层或 `common` 里配 `"textureLevel": 1`，`platforms.<platform>.textureLevel` 可按渠道覆盖。改档只改 profile 一个值再构建。

### 拒绝 ETC2 是一行硬校验

核心实现在 `Assets/Editor/GameNexusTextureCompression.cs`（编辑器和 CI 共用）。`Begin()` 一进来就校验档位格式，白名单里只有 RGBA32 和三个 ASTC 档：

```csharp
if (!Enum.TryParse((string)settings["format"], out TextureImporterFormat format) ||
    !new[] { TextureImporterFormat.RGBA32,
        TextureImporterFormat.ASTC_4x4, TextureImporterFormat.ASTC_6x6, TextureImporterFormat.ASTC_8x8 }.Contains(format))
    throw new InvalidDataException("Uniform WebGL texture format must be RGBA32 or ASTC_4x4/6x6/8x8; ETC2 leaves non-block-aligned sprites uncompressed.");
```

异常消息就是选型理由本身：**ETC2 leaves non-block-aligned sprites uncompressed**。后来者想把格式改回 ETC2，会先撞上这堵墙——文档会被遗忘，抛异常不会。

### 应用与还原：一次事务

CI 的构建接收器把整个构建包在压缩会话里（`ci/common/tools/unity-build/GameNexusBuild.cs`）：

```csharp
using (GameNexusTextureCompression.Begin(req.textureLevel, backup)) Run(req);
```

在 AssetBundle 和播放器构建**之前**应用档位，构建结束（无论成败）都通过 `Dispose` 还原。应用阶段的几个细节：

- 只改 WebGL 平台 override，源图和 Default 平台不动；`maxTextureSize` 取 min(档位上限, 原默认上限)，保证强档也不会超过导入时的原始尺寸上限
- `crunchedCompression` 强制关闭；已经符合目标设置的纹理直接跳过，重复构建幂等
- 遍历的是全工程 `Assets/` 下的 TextureImporter + SpriteAtlasImporter，图集和散图一视同仁

还原是按事务设计的：先把所有将要改动的 `.meta` 文件**逐字节备份**再开始导入，备份清单和变更路径写进 `texture-backup/texture-compression-report.json`。报告用原子写入（先写 `.tmp` 再 `File.Replace`，Windows 索引器或杀毒软件短暂占用文件时按退避重试最多 5 次）。进程被强杀导致还原没有执行的情况也有兜底：保留备份目录，用 Unity CLI 调 `GameNexusTextureCompression.Restore(@"<备份目录>")` 手动恢复——而不是用 Git 一把丢掉可能混入的用户改动。

验证有专门的 `ci/tests/test-texture-compression.cjs`：通过 Unity CLI 检查四个档位的实际格式与尺寸、异常还原、源图及 meta 哈希一致性。

另外补一句认知纠偏：我们 Cocos 时代 CI 里的 `compressImages`（png 级压缩）做的是**磁盘文件压缩**，和这里的 GPU 纹理压缩是两回事。Unity 包里这个开关固定为 `false`——包体大小现在由纹理档位决定，不再靠压 png。

## 六、上线前检查单

- profile 里 `textureLevel` 明确声明，构建报告 `textureCompressionReport` 里有 textureCount / changedCount
- 构建结束后 `texture-backup/` 已还原，`git status` 里没有任何 `.meta` 残留改动
- 真机验证：不支持 ASTC 扩展的设备是否回退解压，运行内存是否在红线内
- 用强档（2/3）时过一遍 UI、字体、Spine 图集的清晰度
- 抽检压缩质量：带 Alpha 的 UI 图和无 Alpha 的场景图分开看
- 想改格式？先读 `Begin()` 里那行异常消息，再想想每个 Sprite 的宽高是不是 4 的倍数

## 参考

- [ASTC 纹理压缩格式详解（知乎）](https://zhuanlan.zhihu.com/p/158740249)
- [你所需要了解的几种纹理压缩格式原理（UWATech）](https://github.com/netoearth/markdown/blob/master/%E4%BD%A0%E6%89%80%E9%9C%80%E8%A6%81%E4%BA%86%E8%A7%A3%E7%9A%84%E5%87%A0%E7%A7%8D%E7%BA%B9%E7%90%86%E5%8E%8B%E7%BC%A9%E6%A0%BC%E5%BC%8F%E5%8E%9F%E7%90%86%20-%20UWATech%E7%9A%84%E4%B8%AA%E4%BA%BA%E7%A9%BA%E9%97%B4%20-%20OSCHINA%20-%20%E4%B8%AD%E6%96%87%E5%BC%80%E6%BA%90%E6%8A%80%E6%9C%AF%E4%BA%A4%E6%B5%81%E7%A4%BE%E5%8C%BA.md)
- [Unity 导入图片尺寸大小和压缩格式的问题（CSDN）](https://blog.csdn.net/linxinfa/article/details/108827197)
- [Unity Texture Import 文档](https://docs.unity3d.com/Manual/class-TextureImporterOverride.html)
