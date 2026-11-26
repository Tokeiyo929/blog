---
title: 优化先测量后动手：没被采样指认的 perf 提交，不进主干
category: "[代码解析]"
date: 2026-11-26
project: 最强斗士急速营救
---

《最强斗士急速营救》要在微信买量，真机帧率不达标。11-25 晚让 AI 通宵优化：15 小时 57 个 perf 提交改了 56 个文件，真机 FPS 纹丝不动，瓶颈一个没定位到，买量延后。

## 一、57 个提交，每一个单看都是对的

57 个提交全带 `perf(` 前缀，按领域分完是这个分布：

| 领域 | 提交数 | 例子 |
| --- | ---: | --- |
| ui | 18 | `b564e62e` 减少布局和字体的重复计算 |
| render | 13 | `879c0e69` 跳过屏幕外陨石本体绘制 |
| combat | 12 | `21046c17` 减少弹道更新的向量分配 |
| vfx | 8 | `feba2475` 复用粒子几何缓冲区视图 |
| physics | 5 | `6db79c0e` 跳过没有接触的陨石求解轮次 |
| wechat | 1 | `38d6c69c` 加速说明随主界面分包加载 |

买量是把钱花在拉新用户上，进来的人一卡就走，帧率不达标，投多少烧多少。从 18:22 的第一个提交排到次日 09:43，平均 16 分钟一个。推它跑起来的理由放在当时一点毛病没有：浪费是真实存在的——每帧的向量分配、屏幕外的陨石照画、面板每次打开重复排版，谁扫一眼代码都能再报出十个。AI 把全仓库的「明显浪费」列成清单逐个修掉，9 个测试文件随提交更新，diff 读上去就是一个勤恳的优化之夜。

漏掉的只有一句话没人问：**它是不是帧耗时的大头？**

## 二、57 个提交，没有一份采样报告

同仓库三周前有一份现成的反例教材。`docs/bullet-performance-20261104.md` 那次的顺序是：先 CPU 采样，确认 `UnityParticleSystem.simulateNative` 和粒子渲染提交占大头；改完再跑三轮 A/B 对照，每轮平均 CPU 从 10.09ms 降到 7.95ms（21.2%），原始数据存进 `temp/bullet-ab-compact.json`，文末还老实记着「未测手机真机、发布包 GPU 时间」。

一夜跑把这套顺序整个倒了过来：先改代码，测试过了，结束。57 个提交附带的 9 个测试文件全是行为正确性回归——`tests/meteor-airflow-culling.cjs` 用 VM 跑编译后的 TS、断言几何输出逐字节一致——没有一个测的是「省了几毫秒」。

挑一条代表看（`6db79c0e`，跳过没有接触的陨石求解轮次）：

```ts
for(let iteration=0;iteration<contactPasses;iteration++){
    let hasContact=false;
    states.sort((a,b)=>a.body.altitude-b.body.altitude||a.body.id.localeCompare(b.body.id));
    for(let i=0;i<states.length;i++)for(let j=i+1;j<states.length;j++){
        // ...碰撞求解，有接触时置 hasContact=true
    }
    // 一整轮没有可移动的对，就提前收工
    if(!hasContact)break;
}
```

单看是正经优化：没接触就不再跑满 6 轮求解。但陨石在一场战斗里到底跑几轮、这 6 轮占一帧多少毫秒，两个数从头到尾是空白。56 个文件里塞满了这种「省一点是一点」，加起来恰好是零。

把这一晚当作一个「版本」答三问：当时的做法是扫浪费清单逐个修；当时觉得合理是因为浪费是真的、修掉只会更快不会更坏；出的事故是 FPS 不动、瓶颈不明、买量延后。错误不在哪一条 diff 里，在顺序里——优化写在了测量之前。

## 三、AI 把写代码变便宜了，没有把找瓶颈变便宜

以前要改 56 个文件，「动手前先想清楚」是成本逼出来的；现在动手成本被压到零，能让人停下来的只剩流程。所以这轮真正的产出只有一条流程不变量：**perf 提交必须带采样背书**。改前同场景同帧数真机采样，改后同条件复测，数字进 docs；拿不出前后两份数据的 perf 提交，一律不进主干。

这条线不是我们的发明。微信小游戏的官方性能体系本身就是一个闭环：评测标准定门槛，真机性能监控和 `wx.reportPerformance` 收线上数据，诊断工具定位，再按启动、运行两条线施策。同平台厂商把「先测后优」做成了平台流程。Unity 的 Profiler 文档原句也是这个意思："You can use this information to decide what you might need to optimize in your application, and to test the performance of changes you make."。再往前，Knuth 1974 年那句话比所有工具都早："We should forget about small efficiencies, say about 97% of them: premature optimization is the root of all evil."——我们一夜修掉的 57 个小效率，大概就在那 97% 里。

瓶颈到今天还没找到，这一晚唯一站得住的产出是确认了流程缺口。第二轮优化从真机采样开始：先拿到帧耗时的大头是谁，再决定动哪里。买量等的是帧率，不是提交数。

## 参考

- [微信小游戏性能优化（微信官方文档）](https://developers.weixin.qq.com/minigame/dev/guide/performance/perf-overview.html)：评测标准、真机性能监控、`wx.reportPerformance`、诊断工具与场景上报分析
- [Profiler introduction（Unity 文档）](https://docs.unity.com/en-us/engine/6000.6/manual/analysis/profiler/introduction)
- [Structured Programming with go to Statements（Knuth, 1974）](https://dl.acm.org/doi/10.1145/356635.356640)
