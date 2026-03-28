"""DedupFilter 核心类 — 三级过滤漏斗检测功能重复的程序。

Level 0: 代码规范化 + AST Hash（<1ms，捕获变量名/注释差异）
Level 1: 行为指纹精确匹配（<1ms，捕获功能等价）
Level 2: 余弦相似度近似匹配（<5ms，捕获近似等价）
"""

from __future__ import annotations

import dataclasses
import hashlib
import time

import numpy as np

from src.dedup.dedup_config import DedupConfig
from src.dedup.probing import compute_fingerprint, PROBING_INSTANCES
from src.normalizer.ast_normalizer import ProgramNormalizer


@dataclasses.dataclass
class DedupResult:
    """单次去重检查的结果。"""
    is_duplicate: bool
    level_caught: int | None       # 被哪一级捕获：0, 1, 2 或 None（未判重）
    time_level0: float             # Level 0 耗时（秒）
    time_level1: float             # Level 1 耗时（秒）
    time_level2: float             # Level 2 耗时（秒）
    fingerprint: tuple | None      # 行为指纹（用于 Level 2 存储）
    is_validation_pass: bool       # 是否为验证样本（即使命中也强制放行）


class DedupFilter:
    """三级去重过滤器。

    在 Sandbox 评估之前快速检测功能重复的程序，节省昂贵的评估时间。
    """

    def __init__(
        self,
        config: DedupConfig,
        template_str: str,
        function_to_evolve: str,
    ):
        """
        Args:
            config: 去重配置
            template_str: 程序模板字符串（用于拼接完整程序以执行探针）
            function_to_evolve: 被进化的函数名（如 'priority'）
        """
        self._config = config
        self._template_str = template_str
        self._function_to_evolve = function_to_evolve
        self._normalizer = ProgramNormalizer()

        # Level 0: AST Hash 集合
        self._code_hash_set: set[str] = set()

        # Level 1: 行为指纹 Hash 集合（精确匹配，零误报）
        self._fingerprint_hash_set: set[str] = set()

        # Level 2: 指纹向量矩阵（用于余弦相似度）
        self._fingerprint_vectors: list[np.ndarray] = []

        # 统计计数器
        self._total_checks = 0

    def check(self, program_str: str, function_body: str) -> DedupResult:
        """对一个候选程序执行三级去重检查。

        Args:
            program_str: 完整可执行的程序字符串
            function_body: 进化函数的函数体（用于 Level 0 规范化）

        Returns:
            DedupResult 记录本次检查的结果和各级耗时
        """
        if not self._config.enabled:
            return DedupResult(
                is_duplicate=False, level_caught=None,
                time_level0=0, time_level1=0, time_level2=0,
                fingerprint=None, is_validation_pass=False,
            )

        self._total_checks += 1

        # 判断是否为验证样本（每 N 次强制放行，用于统计误报率）
        is_validation = (
            self._config.validation_interval > 0
            and self._total_checks % self._config.validation_interval == 0
        )

        time_l0 = time_l1 = time_l2 = 0.0
        fingerprint = None
        caught_l0 = caught_l1 = caught_l2 = False

        # ===== Level 0: 代码规范化 + AST Hash =====
        if self._config.level0_enabled:
            t0 = time.perf_counter()
            caught_l0 = self._check_level0(function_body)
            time_l0 = time.perf_counter() - t0
            if caught_l0 and not is_validation:
                return DedupResult(
                    is_duplicate=True, level_caught=0,
                    time_level0=time_l0, time_level1=0, time_level2=0,
                    fingerprint=None, is_validation_pass=False,
                )

        # ===== Level 1: 行为指纹精确匹配 =====
        if self._config.level1_enabled:
            t1 = time.perf_counter()
            fingerprint = compute_fingerprint(
                program_str, self._function_to_evolve,
                timeout=self._config.probe_timeout_seconds,
            )
            if fingerprint is not None:
                caught_l1 = self._check_level1(fingerprint)
                time_l1 = time.perf_counter() - t1
                if caught_l1 and not is_validation:
                    return DedupResult(
                        is_duplicate=True, level_caught=1,
                        time_level0=time_l0, time_level1=time_l1, time_level2=0,
                        fingerprint=fingerprint, is_validation_pass=False,
                    )
            else:
                time_l1 = time.perf_counter() - t1

        # ===== Level 2: 余弦相似度近似匹配 =====
        if self._config.level2_enabled and fingerprint is not None:
            t2 = time.perf_counter()
            caught_l2 = self._check_level2(fingerprint)
            time_l2 = time.perf_counter() - t2
            if caught_l2 and not is_validation:
                return DedupResult(
                    is_duplicate=True, level_caught=2,
                    time_level0=time_l0, time_level1=time_l1, time_level2=time_l2,
                    fingerprint=fingerprint, is_validation_pass=False,
                )

        # ===== 判断是否被任何级别捕获 =====
        was_caught = caught_l0 or caught_l1 or caught_l2

        # 只有真正的新程序才注册（避免验证样本重复注册导致自我匹配）
        if not was_caught:
            self._register(function_body, fingerprint)

        # 推导 level_caught（验证样本用，记录"本应被哪级捕获"）
        level_caught = None
        if was_caught:
            level_caught = 0 if caught_l0 else (1 if caught_l1 else 2)

        return DedupResult(
            is_duplicate=was_caught,
            level_caught=level_caught,
            time_level0=time_l0, time_level1=time_l1, time_level2=time_l2,
            fingerprint=fingerprint,
            is_validation_pass=is_validation,
        )

    # ------------------------------------------------------------------
    # Level 0: 代码规范化 + AST Hash
    # ------------------------------------------------------------------

    def _check_level0(self, function_body: str) -> bool:
        """检查代码 AST Hash 是否已存在。"""
        ast_hash = self._compute_ast_hash(function_body)
        if ast_hash is None:
            return False  # 语法错误，跳过此级
        return ast_hash in self._code_hash_set

    def _compute_ast_hash(self, function_body: str) -> str | None:
        """将函数体包装为完整函数后计算 AST Hash。"""
        try:
            # 包装为完整函数定义，ProgramNormalizer 需要合法的 Python 代码
            # 注意：硬编码了 (item, bins) 参数名。AST 规范化会忽略类型注解，
            # 所以不需要写 (item: float, bins: np.ndarray)。
            # 如果未来函数签名参数名变化，需同步修改此处。
            wrapped = f"def {self._function_to_evolve}(item, bins):\n{function_body}"
            normalized = self._normalizer.normalize(wrapped)
            return normalized.ast_hash
        except (SyntaxError, Exception):
            return None

    # ------------------------------------------------------------------
    # Level 1: 行为指纹精确匹配
    # ------------------------------------------------------------------

    def _check_level1(self, fingerprint: tuple[int, ...]) -> bool:
        """检查指纹 Hash 是否已存在（O(1) 查找，零误报）。"""
        fp_hash = self._hash_fingerprint(fingerprint)
        return fp_hash in self._fingerprint_hash_set

    @staticmethod
    def _hash_fingerprint(fingerprint: tuple[int, ...]) -> str:
        """将指纹元组转为 SHA256 Hash 字符串。"""
        return hashlib.sha256(str(fingerprint).encode()).hexdigest()

    # ------------------------------------------------------------------
    # Level 2: 余弦相似度近似匹配
    # ------------------------------------------------------------------

    def _check_level2(self, fingerprint: tuple[int, ...]) -> bool:
        """检查指纹向量与已存向量的最大余弦相似度是否超过阈值。"""
        if not self._fingerprint_vectors:
            return False
        vec = self._fingerprint_to_vector(fingerprint)
        # 矩阵乘法计算余弦相似度（所有向量已 L2 归一化）
        matrix = np.array(self._fingerprint_vectors)
        similarities = matrix @ vec
        return float(np.max(similarities)) >= self._config.cosine_threshold

    @staticmethod
    def _fingerprint_to_vector(fingerprint: tuple[int, ...]) -> np.ndarray:
        """将指纹元组转为 L2 归一化的浮点向量。"""
        vec = np.array(fingerprint, dtype=np.float64)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    # ------------------------------------------------------------------
    # 注册新程序（通过所有级别后调用）
    # ------------------------------------------------------------------

    def _register(self, function_body: str, fingerprint: tuple[int, ...] | None) -> None:
        """将新程序注册到各级索引中。"""
        # Level 0: 注册 AST Hash
        ast_hash = self._compute_ast_hash(function_body)
        if ast_hash is not None:
            self._code_hash_set.add(ast_hash)

        # Level 1 & 2: 注册指纹
        if fingerprint is not None:
            fp_hash = self._hash_fingerprint(fingerprint)
            self._fingerprint_hash_set.add(fp_hash)
            vec = self._fingerprint_to_vector(fingerprint)
            self._fingerprint_vectors.append(vec)
