"""资源质量评分服务 - 对抓取的资源进行质量评估和排序。

功能：
1. 多维度质量评分
2. 资源去重
3. 智能排序
4. 个性化推荐（预留）

输入：资源列表
输出：排序后的资源列表（含质量评分）

验收标准：
- ✅ 资源去重
- ✅ 质量评分
- ✅ 智能排序
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class ResourceQualityTier(Enum):
    """资源质量分级。"""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"  # 70-89
    FAIR = "fair"  # 50-69
    POOR = "poor"  # < 50


@dataclass
class QualityMetrics:
    """质量评估指标。"""
    content_quality: float = 0.0  # 内容质量 (0-1)
    authority: float = 0.0  # 权威性 (0-1)
    freshness: float = 0.0  # 时效性 (0-1)
    engagement: float = 0.0  # 参与度 (0-1)
    completeness: float = 0.0  # 完整性 (0-1)
    
    def weighted_score(self, weights: Dict[str, float] = None) -> float:
        """计算加权总分。
        
        Args:
            weights: 各指标权重，默认平均分配
        
        Returns:
            float: 加权总分 (0-1)
        """
        if weights is None:
            weights = {
                "content_quality": 0.35,
                "authority": 0.25,
                "freshness": 0.15,
                "engagement": 0.15,
                "completeness": 0.10
            }
        
        score = (
            weights.get("content_quality", 0.2) * self.content_quality +
            weights.get("authority", 0.2) * self.authority +
            weights.get("freshness", 0.2) * self.freshness +
            weights.get("engagement", 0.2) * self.engagement +
            weights.get("completeness", 0.2) * self.completeness
        )
        return min(max(score, 0.0), 1.0)
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典格式。"""
        return {
            "content_quality": self.content_quality,
            "authority": self.authority,
            "freshness": self.freshness,
            "engagement": self.engagement,
            "completeness": self.completeness,
            "overall_score": self.weighted_score()
        }


@dataclass
class RankedResource:
    """排序后的资源。"""
    id: str
    title: str
    url: str
    resource_type: str
    quality_score: float
    quality_tier: ResourceQualityTier
    metrics: QualityMetrics
    duration: Optional[int] = None
    description: str = ""
    author: str = ""
    publish_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "type": self.resource_type,
            "quality_score": self.quality_score,
            "quality_tier": self.quality_tier.value,
            "metrics": self.metrics.to_dict(),
            "duration": self.duration,
            "description": self.description,
            "author": self.author,
            "publish_date": self.publish_date.isoformat() if self.publish_date else None,
            "tags": self.tags,
            "metadata": self.metadata
        }


class ContentQualityAnalyzer:
    """内容质量分析器。"""
    
    def analyze(self, title: str, description: str, metadata: Dict[str, Any] = None) -> float:
        """分析内容质量。
        
        Args:
            title: 资源标题
            description: 资源描述
            metadata: 额外元数据
        
        Returns:
            float: 内容质量评分 (0-1)
        """
        score = 0.0
        
        # 标题质量（长度、关键词）
        title_score = self._analyze_title(title)
        score += title_score * 0.3
        
        # 描述质量（长度、信息量）
        desc_score = self._analyze_description(description)
        score += desc_score * 0.4
        
        # 元数据质量
        meta_score = self._analyze_metadata(metadata or {})
        score += meta_score * 0.3
        
        return min(score, 1.0)
    
    def _analyze_title(self, title: str) -> float:
        """分析标题质量。"""
        score = 0.0
        
        # 长度评分（理想 20-50 字）
        title_len = len(title)
        if 20 <= title_len <= 50:
            score += 0.4
        elif 10 <= title_len <= 80:
            score += 0.2
        
        # 包含关键词（教程、指南、详解等）
        keywords = ["教程", "指南", "详解", "入门", "进阶", "实战", "教程", "tutorial", "guide"]
        if any(kw in title.lower() for kw in keywords):
            score += 0.3
        
        # 不包含标题党词汇
        clickbait = ["震惊", "必看", "秒懂", "100%", "最"]
        if not any(kw in title for kw in clickbait):
            score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_description(self, description: str) -> float:
        """分析描述质量。"""
        score = 0.0
        
        # 长度评分（理想 100-500 字）
        desc_len = len(description)
        if 100 <= desc_len <= 500:
            score += 0.5
        elif 50 <= desc_len <= 1000:
            score += 0.3
        
        # 包含结构化信息
        if any(marker in description for marker in ["\n", "•", "-", "1.", "●"]):
            score += 0.2
        
        # 包含技术关键词
        tech_keywords = ["代码", "示例", "实践", "案例", "源码", "github", "api"]
        if any(kw in description.lower() for kw in tech_keywords):
            score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_metadata(self, metadata: Dict[str, Any]) -> float:
        """分析元数据质量。"""
        score = 0.0
        
        # 有播放量/阅读量
        if "play_count" in metadata or "view_count" in metadata:
            score += 0.3
        
        # 有点赞/收藏
        if "favorites" in metadata or "likes" in metadata:
            score += 0.3
        
        # 有评论/弹幕
        if "danmaku" in metadata or "comments" in metadata:
            score += 0.2
        
        # 有时长信息
        if "duration" in metadata:
            score += 0.2
        
        return min(score, 1.0)


class AuthorityAnalyzer:
    """权威性分析器。"""
    
    # 权威域名列表
    AUTHORITY_DOMAINS = {
        "high": [
            "youtube.com", "bilibili.com",  # 主流视频平台
            "github.com", "gitlab.com",  # 代码托管
            "stackoverflow.com", "medium.com",  # 技术社区
            "zhihu.com", "juejin.cn",  # 中文技术社区
            "wikipedia.org", "baike.baidu.com",  # 百科
        ],
        "medium": [
            "csdn.net", "blog.csdn.net",
            "cnblogs.com",
            "segmentfault.com",
            "imooc.com", "coursera.org", "udemy.com",  # 教育平台
        ],
        "low": [
            "blogspot.com", "wordpress.com",  # 个人博客平台
        ]
    }
    
    def analyze(self, url: str, author: str = "", metadata: Dict[str, Any] = None) -> float:
        """分析资源权威性。
        
        Args:
            url: 资源 URL
            author: 作者名
            metadata: 额外元数据
        
        Returns:
            float: 权威性评分 (0-1)
        """
        score = 0.0
        
        # 域名权威性
        domain_score = self._analyze_domain(url)
        score += domain_score * 0.6
        
        # 作者权威性
        author_score = self._analyze_author(author, metadata or {})
        score += author_score * 0.4
        
        return min(score, 1.0)
    
    def _analyze_domain(self, url: str) -> float:
        """分析域名权威性。"""
        import re
        match = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", url)
        if not match:
            return 0.5
        
        domain = match.group(1).lower()
        
        for tier, domains in self.AUTHORITY_DOMAINS.items():
            if any(d in domain for d in domains):
                if tier == "high":
                    return 1.0
                elif tier == "medium":
                    return 0.7
                else:
                    return 0.5
        
        # 未知域名
        return 0.5
    
    def _analyze_author(self, author: str, metadata: Dict[str, Any]) -> float:
        """分析作者权威性。"""
        score = 0.0
        
        # 有作者名
        if author and len(author) > 2:
            score += 0.3
        
        # 认证作者（如果有标识）
        if metadata:
            if metadata.get("verified"):
                score += 0.4
            if metadata.get("follower_count", 0) > 10000:
                score += 0.3
        
        return min(score, 1.0)


class FreshnessAnalyzer:
    """时效性分析器。"""
    
    def analyze(self, publish_date: Optional[datetime], metadata: Dict[str, Any] = None) -> float:
        """分析资源时效性。
        
        Args:
            publish_date: 发布日期
            metadata: 额外元数据（可包含 last_update 等）
        
        Returns:
            float: 时效性评分 (0-1)
        """
        if not publish_date:
            # 没有日期信息，根据元数据推测
            if metadata and metadata.get("last_update"):
                try:
                    publish_date = datetime.fromisoformat(metadata["last_update"])
                except Exception:
                    return 0.5
            else:
                return 0.5
        
        # 计算发布时间距今的天数
        days_old = (datetime.now() - publish_date).days
        
        # 评分标准：
        # 0-30 天：1.0
        # 30-90 天：0.8
        # 90-180 天：0.6
        # 180-365 天：0.4
        # > 365 天：0.2
        
        if days_old <= 30:
            return 1.0
        elif days_old <= 90:
            return 0.8
        elif days_old <= 180:
            return 0.6
        elif days_old <= 365:
            return 0.4
        else:
            return 0.2


class EngagementAnalyzer:
    """参与度分析器。"""
    
    def analyze(self, metadata: Dict[str, Any]) -> float:
        """分析资源参与度。
        
        Args:
            metadata: 元数据（包含播放量、点赞、评论等）
        
        Returns:
            float: 参与度评分 (0-1)
        """
        score = 0.0
        
        # 播放量/阅读量
        play_count = metadata.get("play_count", metadata.get("view_count", 0))
        if play_count > 100000:
            score += 0.4
        elif play_count > 10000:
            score += 0.3
        elif play_count > 1000:
            score += 0.2
        elif play_count > 100:
            score += 0.1
        
        # 点赞/收藏
        favorites = metadata.get("favorites", metadata.get("likes", 0))
        if favorites > 10000:
            score += 0.3
        elif favorites > 1000:
            score += 0.2
        elif favorites > 100:
            score += 0.1
        
        # 评论/弹幕
        comments = metadata.get("comments", metadata.get("danmaku", 0))
        if comments > 1000:
            score += 0.3
        elif comments > 100:
            score += 0.2
        elif comments > 10:
            score += 0.1
        
        return min(score, 1.0)


class CompletenessAnalyzer:
    """完整性分析器。"""
    
    def analyze(self, duration: Optional[int], resource_type: str, metadata: Dict[str, Any] = None) -> float:
        """分析资源完整性。
        
        Args:
            duration: 时长（秒）
            resource_type: 资源类型
            metadata: 额外元数据
        
        Returns:
            float: 完整性评分 (0-1)
        """
        score = 0.0
        
        # 时长评分（根据资源类型）
        if duration:
            if resource_type in ["bilibili_video", "youtube_video"]:
                # 视频：5-30 分钟最佳
                minutes = duration / 60
                if 5 <= minutes <= 30:
                    score += 0.5
                elif 30 < minutes <= 60:
                    score += 0.4
                elif 2 <= minutes < 5:
                    score += 0.3
                elif minutes > 60:
                    score += 0.3  # 长视频可能是系列教程
            else:
                # 文章：阅读时间 5-20 分钟最佳
                minutes = duration / 60
                if 5 <= minutes <= 20:
                    score += 0.5
                elif 2 <= minutes <= 30:
                    score += 0.3
        
        # 系列内容加分
        if metadata:
            if metadata.get("series") or metadata.get("playlist"):
                score += 0.3
            
            # 有配套资源（代码、课件等）
            if metadata.get("has_code") or metadata.get("has_slides"):
                score += 0.2
        
        return min(score, 1.0)


class ResourceDeduplicator:
    """资源去重器。"""
    
    def __init__(self, strategy: str = "url"):
        """初始化去重器。
        
        Args:
            strategy: 去重策略，'url' 或 'content'
        """
        self.strategy = strategy
        self.seen = set()
    
    def deduplicate(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重资源列表。
        
        Args:
            resources: 资源列表
        
        Returns:
            List[Dict[str, Any]]: 去重后的资源列表
        """
        unique = []
        
        for resource in resources:
            key = self._generate_key(resource)
            if key not in self.seen:
                self.seen.add(key)
                unique.append(resource)
        
        return unique
    
    def _generate_key(self, resource: Dict[str, Any]) -> str:
        """生成去重键。"""
        if self.strategy == "url":
            return resource.get("url", "")
        elif self.strategy == "content":
            # 基于标题 + 描述生成哈希
            content = f"{resource.get('title', '')}{resource.get('description', '')}"
            return hashlib.md5(content.encode()).hexdigest()
        else:
            return resource.get("url", "")
    
    def reset(self):
        """重置去重状态。"""
        self.seen.clear()


class ResourceRanker:
    """资源排序器。"""
    
    def __init__(self):
        self.content_analyzer = ContentQualityAnalyzer()
        self.authority_analyzer = AuthorityAnalyzer()
        self.freshness_analyzer = FreshnessAnalyzer()
        self.engagement_analyzer = EngagementAnalyzer()
        self.completeness_analyzer = CompletenessAnalyzer()
        self.deduplicator = ResourceDeduplicator()
    
    def rank(self, resources: List[Dict[str, Any]], 
             weights: Dict[str, float] = None,
             deduplicate: bool = True) -> List[RankedResource]:
        """对资源进行评分和排序。
        
        Args:
            resources: 资源列表
            weights: 各指标权重
            deduplicate: 是否去重
        
        Returns:
            List[RankedResource]: 排序后的资源列表
        """
        # 去重
        if deduplicate:
            resources = self.deduplicator.deduplicate(resources)
        
        ranked_resources = []
        
        for idx, resource in enumerate(resources):
            # 计算各项指标
            metrics = self._calculate_metrics(resource)
            overall_score = metrics.weighted_score(weights)
            
            # 确定质量等级
            quality_tier = self._get_quality_tier(overall_score)
            
            # 创建排序后的资源对象
            ranked = RankedResource(
                id=resource.get("id", f"res_{idx}_{hashlib.md5(resource.get('url', '').encode()).hexdigest()[:8]}"),
                title=resource.get("title", ""),
                url=resource.get("url", ""),
                resource_type=resource.get("type", "other"),
                quality_score=overall_score,
                quality_tier=quality_tier,
                metrics=metrics,
                duration=resource.get("duration"),
                description=resource.get("description", ""),
                author=resource.get("author", ""),
                publish_date=resource.get("publish_date"),
                tags=resource.get("tags", []),
                metadata=resource.get("metadata", {})
            )
            
            ranked_resources.append(ranked)
        
        # 按质量评分降序排序
        ranked_resources.sort(key=lambda r: r.quality_score, reverse=True)
        
        return ranked_resources
    
    def _calculate_metrics(self, resource: Dict[str, Any]) -> QualityMetrics:
        """计算各项质量指标。"""
        return QualityMetrics(
            content_quality=self.content_analyzer.analyze(
                resource.get("title", ""),
                resource.get("description", ""),
                resource.get("metadata", {})
            ),
            authority=self.authority_analyzer.analyze(
                resource.get("url", ""),
                resource.get("author", ""),
                resource.get("metadata", {})
            ),
            freshness=self.freshness_analyzer.analyze(
                resource.get("publish_date"),
                resource.get("metadata", {})
            ),
            engagement=self.engagement_analyzer.analyze(
                resource.get("metadata", {})
            ),
            completeness=self.completeness_analyzer.analyze(
                resource.get("duration"),
                resource.get("type", "other"),
                resource.get("metadata", {})
            )
        )
    
    def _get_quality_tier(self, score: float) -> ResourceQualityTier:
        """根据评分确定质量等级。"""
        if score >= 0.9:
            return ResourceQualityTier.EXCELLENT
        elif score >= 0.7:
            return ResourceQualityTier.GOOD
        elif score >= 0.5:
            return ResourceQualityTier.FAIR
        else:
            return ResourceQualityTier.POOR


class ResourceRankerService:
    """资源评分服务 - 统一入口。"""
    
    def __init__(self):
        self.ranker = ResourceRanker()
    
    def rank_resources(self, resources: List[Dict[str, Any]], 
                       weights: Dict[str, float] = None,
                       top_n: Optional[int] = None) -> List[RankedResource]:
        """对资源进行评分和排序。
        
        Args:
            resources: 资源列表
            weights: 各指标权重
            top_n: 返回前 N 个，None 表示全部
        
        Returns:
            List[RankedResource]: 排序后的资源列表
        """
        ranked = self.ranker.rank(resources, weights)
        
        if top_n:
            ranked = ranked[:top_n]
        
        return ranked
    
    def get_recommendations(self, resources: List[Dict[str, Any]], 
                           user_preferences: Dict[str, Any] = None,
                           top_n: int = 10) -> List[RankedResource]:
        """获取推荐资源（个性化）。
        
        Args:
            resources: 资源列表
            user_preferences: 用户偏好
            top_n: 返回数量
        
        Returns:
            List[RankedResource]: 推荐资源列表
        """
        # 根据用户偏好调整权重
        weights = self._customize_weights(user_preferences)
        
        ranked = self.rank_resources(resources, weights, top_n)
        
        return ranked
    
    def _customize_weights(self, preferences: Dict[str, Any] = None) -> Dict[str, float]:
        """根据用户偏好定制权重。"""
        # 默认权重
        weights = {
            "content_quality": 0.35,
            "authority": 0.25,
            "freshness": 0.15,
            "engagement": 0.15,
            "completeness": 0.10
        }
        
        if not preferences:
            return weights
        
        # 根据偏好调整
        if preferences.get("prefer_fresh"):
            weights["freshness"] = 0.3
            weights["content_quality"] = 0.25
        
        if preferences.get("prefer_authoritative"):
            weights["authority"] = 0.35
            weights["engagement"] = 0.10
        
        if preferences.get("prefer_complete"):
            weights["completeness"] = 0.2
            weights["freshness"] = 0.1
        
        return weights


# 便捷函数
def rank_resources(resources: List[Dict[str, Any]], top_n: Optional[int] = None) -> List[RankedResource]:
    """便捷函数：资源评分排序。"""
    service = ResourceRankerService()
    return service.rank_resources(resources, top_n=top_n)


def get_recommendations(resources: List[Dict[str, Any]], 
                       preferences: Dict[str, Any] = None,
                       top_n: int = 10) -> List[RankedResource]:
    """便捷函数：获取推荐资源。"""
    service = ResourceRankerService()
    return service.get_recommendations(resources, preferences, top_n)
