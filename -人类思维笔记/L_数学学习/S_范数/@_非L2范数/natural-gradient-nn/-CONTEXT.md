# -CONTEXT — 自然梯度法 / 信息几何 NN 实验

## 这是什么
探索"真正在非 L2 参数空间中训练 NN"的正确数学框架：**自然梯度法（Natural Gradient）**。

起因：`0_Sonnet的思考.md` 操作 4 — 用户问"在曼哈顿空间训练 NN"，而豆包答的是 L1 损失函数，并非参数空间几何的变更。正确框架是 Amari 1998 的信息几何。

## 核心数学框架（留给未来实现者参考）

普通梯度下降假设参数空间是欧氏的（隐式 L2 度量）：
$$\theta_{t+1} = \theta_t - \alpha \nabla L(\theta)$$

自然梯度法用 Fisher 信息矩阵 $G(\theta)$ 作为黎曼度量张量：
$$\theta_{t+1} = \theta_t - \alpha \, G(\theta)^{-1} \nabla L(\theta)$$

- $G(\theta)_{ij} = \mathbb{E}\left[\frac{\partial \log p(x|\theta)}{\partial \theta_i} \frac{\partial \log p(x|\theta)}{\partial \theta_j}\right]$
- 实用近似：K-FAC（Kronecker-Factored Approximate Curvature）

## 技术路线（待实现时参考）
1. 读 Amari 1998 原始论文："Natural Gradient Works Efficiently in Learning"
2. 工具：`jax`（自动微分，方便计算 Fisher）或 PyTorch + `backpack` 库
3. 对比实验：普通 Adam vs 自然梯度（K-FAC 近似）在小规模 MLP 上的收敛速度
4. 可视化：损失曲线 + 参数轨迹（PCA 降维到 2D）

## 跨 session 提醒
- 这是研究级方向，不是工程实用方向
- 完整 Fisher 矩阵计算复杂度是 $O(N^2)$，N 为参数数，需用 K-FAC 等近似
- 有限维向量空间的所有范数拓扑等价（基础定理）——所以"换范数"改的是优化几何，不是模型的表达能力
- 与 L1 空间的联系：L1 Wasserstein 距离 / Optimal Transport 是另一个"非 L2 空间 NN"方向

## 当前状态
- ✅ -CONTEXT.md 建立（2026-03-31）
- ⏳ 待实现，优先级低于 lora-dechirp-verify 和 pid-nn-norm-compare

## 下一步
- ⏳ 👆 读 Amari 1998 原文（可用 defuddle skill 提取 PDF/DOI 内容）
- ⏳ 最小实验：3 层 MLP + K-FAC 近似自然梯度
