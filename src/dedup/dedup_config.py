"""去重模块配置 — 控制三级过滤漏斗的开关和参数。"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class DedupConfig:
    """三级去重漏斗的配置参数。

    Attributes:
        enabled: 总开关，False 则完全跳过去重
        level0_enabled: Level 0 — 代码规范化 + AST Hash
        level1_enabled: Level 1 — 行为指纹精确匹配
        level2_enabled: Level 2 — 余弦相似度近似匹配
        cosine_threshold: Level 2 判重阈值（越高越保守，0.98 表示几乎完全相同才判重）
        probe_timeout_seconds: 单个探针执行的超时秒数
        validation_interval: 每 N 个样本强制放行一个"命中"样本做验证（用于误报率统计）
    """
    enabled: bool = True
    level0_enabled: bool = True
    level1_enabled: bool = True
    level2_enabled: bool = True
    cosine_threshold: float = 0.98
    probe_timeout_seconds: int = 5
    validation_interval: int = 50
