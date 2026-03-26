"""资源质量评分服务测试。

测试覆盖：
1. 内容质量分析
2. 权威性分析
3. 时效性分析
4. 参与度分析
5. 完整性分析
6. 资源去重
7. 智能排序
8. 集成测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from edict.backend.app.services.resource_ranker import (
    ResourceRankerService,
    ResourceRanker,
    ContentQualityAnalyzer,
    AuthorityAnalyzer,
    FreshnessAnalyzer,
    EngagementAnalyzer,
    CompletenessAnalyzer,
    ResourceDeduplicator,
    QualityMetrics,
    RankedResource,
    ResourceQualityTier,
    rank_resources,
    get_recommendations,
)


class TestQualityMetrics:
    """测试质量评估指标。"""
    
    def test_metrics_creation(self):
        """测试指标创建。"""
        metrics = QualityMetrics(
            content_quality=0.8,
            authority=0.9,
            freshness=0.7,
            engagement=0.6,
            completeness=0.5
        )
        
        assert metrics.content_quality == 0.8
        assert metrics.authority == 0.9
    
    def test_weighted_score_default(self):
        """测试默认权重评分。"""
        metrics = QualityMetrics(
            content_quality=1.0,
            authority=1.0,
            freshness=1.0,
            engagement=1.0,
            completeness=1.0
        )
        
        score = metrics.weighted_score()
        
        assert 0.0 <= score <= 1.0
        assert score == 1.0  # 全满分
    
    def test_weighted_score_custom(self):
        """测试自定义权重评分。"""
        metrics = QualityMetrics(
            content_quality=1.0,
            authority=0.0,
            freshness=0.0,
            engagement=0.0,
            completeness=0.0
        )
        
        weights = {"content_quality": 1.0, "authority": 0, "freshness": 0, "engagement": 0, "completeness": 0}
        score = metrics.weighted_score(weights)
        
        assert score == 1.0
    
    def test_weighted_score_bounds(self):
        """测试评分边界。"""
        metrics = QualityMetrics(
            content_quality=2.0,  # 超出范围
            authority=-1.0,  # 负数
            freshness=0.5,
            engagement=0.5,
            completeness=0.5
        )
        
        score = metrics.weighted_score()
        
        assert 0.0 <= score <= 1.0
    
    def test_to_dict(self):
        """测试转字典。"""
        metrics = QualityMetrics(content_quality=0.8, authority=0.7, freshness=0.6, engagement=0.5, completeness=0.4)
        
        data = metrics.to_dict()
        
        assert "content_quality" in data
        assert "overall_score" in data
        assert data["content_quality"] == 0.8


class TestContentQualityAnalyzer:
    """测试内容质量分析器。"""
    
    def test_analyze_good_title(self):
        """测试好标题分析。"""
        analyzer = ContentQualityAnalyzer()
        
        score = analyzer._analyze_title("Python 入门教程：从基础到实战")
        
        assert score > 0.5  # 包含关键词，长度适中
    
    def test_analyze_clickbait_title(self):
        """测试标题党标题分析。"""
        analyzer = ContentQualityAnalyzer()
        
        score = analyzer._analyze_title("震惊！100% 必看的 Python 教程")
        
        assert score < 0.7  # 包含标题党词汇，扣分
    
    def test_analyze_short_title(self):
        """测试短标题分析。"""
        analyzer = ContentQualityAnalyzer()
        
        score = analyzer._analyze_title("教程")
        
        assert score < 0.5  # 太短
    
    def test_analyze_good_description(self):
        """测试好描述分析。"""
        analyzer = ContentQualityAnalyzer()
        
        desc = "本教程涵盖 Python 基础语法、数据结构、函数编程等内容。\n" * 20
        desc += "包含大量代码示例和实践案例。"
        
        score = analyzer._analyze_description(desc)
        
        assert score > 0.5
    
    def test_analyze_short_description(self):
        """测试短描述分析。"""
        analyzer = ContentQualityAnalyzer()
        
        score = analyzer._analyze_description("这是一个教程")
        
        assert score < 0.5
    
    def test_analyze_metadata(self):
        """测试元数据分析。"""
        analyzer = ContentQualityAnalyzer()
        
        metadata = {
            "play_count": 100000,
            "favorites": 5000,
            "danmaku": 1000,
            "duration": 1800
        }
        
        score = analyzer._analyze_metadata(metadata)
        
        assert score > 0.8  # 元数据完整
    
    def test_analyze_empty_metadata(self):
        """测试空元数据分析。"""
        analyzer = ContentQualityAnalyzer()
        
        score = analyzer._analyze_metadata({})
        
        assert score == 0.0
    
    def test_analyze_full(self):
        """测试完整内容分析。"""
        analyzer = ContentQualityAnalyzer()
        
        score = analyzer.analyze(
            title="Python 教程：从入门到精通",
            description="详细内容" * 100,
            metadata={"play_count": 10000}
        )
        
        assert 0.0 <= score <= 1.0


class TestAuthorityAnalyzer:
    """测试权威性分析器。"""
    
    def test_analyze_high_authority_domain(self):
        """测试高权威域名分析。"""
        analyzer = AuthorityAnalyzer()
        
        score = analyzer._analyze_domain("https://www.youtube.com/watch?v=xxx")
        
        assert score == 1.0
    
    def test_analyze_medium_authority_domain(self):
        """测试中等权威域名分析。"""
        analyzer = AuthorityAnalyzer()
        
        score = analyzer._analyze_domain("https://blog.csdn.net/article/xxx")
        
        assert score == 0.7
    
    def test_analyze_unknown_domain(self):
        """测试未知域名分析。"""
        analyzer = AuthorityAnalyzer()
        
        score = analyzer._analyze_domain("https://unknown-site.com/page")
        
        assert score == 0.5
    
    def test_analyze_author_with_followers(self):
        """测试有粉丝数的作者分析。"""
        analyzer = AuthorityAnalyzer()
        
        metadata = {"follower_count": 50000, "verified": True}
        score = analyzer._analyze_author("知名 UP 主", metadata)
        
        assert score > 0.7
    
    def test_analyze_full_authority(self):
        """测试完整权威性分析。"""
        analyzer = AuthorityAnalyzer()
        
        score = analyzer.analyze(
            url="https://www.bilibili.com/video/BV123",
            author="教程 UP 主",
            metadata={"verified": True}
        )
        
        assert 0.0 <= score <= 1.0


class TestFreshnessAnalyzer:
    """测试时效性分析器。"""
    
    def test_analyze_very_fresh(self):
        """测试非常新的资源。"""
        analyzer = FreshnessAnalyzer()
        
        recent_date = datetime.now() - timedelta(days=7)
        score = analyzer.analyze(recent_date)
        
        assert score == 1.0
    
    def test_analyze_fresh(self):
        """测试较新的资源。"""
        analyzer = FreshnessAnalyzer()
        
        recent_date = datetime.now() - timedelta(days=60)
        score = analyzer.analyze(recent_date)
        
        assert score == 0.8
    
    def test_analyze_moderate(self):
        """测试中等时效的资源。"""
        analyzer = FreshnessAnalyzer()
        
        moderate_date = datetime.now() - timedelta(days=120)
        score = analyzer.analyze(moderate_date)
        
        assert score == 0.6
    
    def test_analyze_old(self):
        """测试较旧的资源。"""
        analyzer = FreshnessAnalyzer()
        
        old_date = datetime.now() - timedelta(days=400)
        score = analyzer.analyze(old_date)
        
        assert score == 0.2
    
    def test_analyze_no_date(self):
        """测试无日期资源。"""
        analyzer = FreshnessAnalyzer()
        
        score = analyzer.analyze(None)
        
        assert score == 0.5


class TestEngagementAnalyzer:
    """测试参与度分析器。"""
    
    def test_analyze_high_engagement(self):
        """测试高参与度。"""
        analyzer = EngagementAnalyzer()
        
        metadata = {
            "play_count": 1000000,
            "favorites": 50000,
            "comments": 10000
        }
        
        score = analyzer.analyze(metadata)
        
        assert score > 0.8
    
    def test_analyze_medium_engagement(self):
        """测试中等参与度。"""
        analyzer = EngagementAnalyzer()
        
        metadata = {
            "play_count": 5000,
            "favorites": 500,
            "comments": 50
        }
        
        score = analyzer.analyze(metadata)
        
        assert 0.3 <= score <= 0.7
    
    def test_analyze_low_engagement(self):
        """测试低参与度。"""
        analyzer = EngagementAnalyzer()
        
        metadata = {
            "play_count": 50,
            "favorites": 0,
            "comments": 0
        }
        
        score = analyzer.analyze(metadata)
        
        assert score < 0.3
    
    def test_analyze_empty_metadata(self):
        """测试空元数据。"""
        analyzer = EngagementAnalyzer()
        
        score = analyzer.analyze({})
        
        assert score == 0.0


class TestCompletenessAnalyzer:
    """测试完整性分析器。"""
    
    def test_analyze_video_optimal_duration(self):
        """测试视频最佳时长。"""
        analyzer = CompletenessAnalyzer()
        
        # 15 分钟视频
        score = analyzer.analyze(duration=900, resource_type="bilibili_video")
        
        assert score >= 0.5
    
    def test_analyze_video_too_short(self):
        """测试视频太短。"""
        analyzer = CompletenessAnalyzer()
        
        # 1 分钟视频
        score = analyzer.analyze(duration=60, resource_type="bilibili_video")
        
        assert score < 0.5
    
    def test_analyze_video_too_long(self):
        """测试视频太长。"""
        analyzer = CompletenessAnalyzer()
        
        # 3 小时视频
        score = analyzer.analyze(duration=10800, resource_type="bilibili_video")
        
        assert score < 0.5
    
    def test_analyze_with_series(self):
        """测试系列内容。"""
        analyzer = CompletenessAnalyzer()
        
        metadata = {"series": True, "has_code": True}
        score = analyzer.analyze(duration=600, resource_type="bilibili_video", metadata=metadata)
        
        assert score > 0.5  # 系列加分
    
    def test_analyze_no_duration(self):
        """测试无时长信息。"""
        analyzer = CompletenessAnalyzer()
        
        score = analyzer.analyze(duration=None, resource_type="article")
        
        assert score == 0.0


class TestResourceDeduplicator:
    """测试资源去重器。"""
    
    def test_deduplicate_by_url(self):
        """测试基于 URL 去重。"""
        deduplicator = ResourceDeduplicator(strategy="url")
        
        resources = [
            {"title": "资源 1", "url": "https://example.com/1"},
            {"title": "资源 2", "url": "https://example.com/2"},
            {"title": "资源 1 重复", "url": "https://example.com/1"},
        ]
        
        unique = deduplicator.deduplicate(resources)
        
        assert len(unique) == 2
    
    def test_deduplicate_by_content(self):
        """测试基于内容去重。"""
        deduplicator = ResourceDeduplicator(strategy="content")
        
        resources = [
            {"title": "相同标题", "description": "相同描述", "url": "https://a.com"},
            {"title": "不同标题", "description": "不同描述", "url": "https://b.com"},
            {"title": "相同标题", "description": "相同描述", "url": "https://c.com"},
        ]
        
        unique = deduplicator.deduplicate(resources)
        
        assert len(unique) == 2
    
    def test_reset(self):
        """测试重置。"""
        deduplicator = ResourceDeduplicator()
        
        resources = [{"title": "测试", "url": "https://example.com"}]
        deduplicator.deduplicate(resources)
        
        assert len(deduplicator.seen) > 0
        
        deduplicator.reset()
        
        assert len(deduplicator.seen) == 0


class TestResourceRanker:
    """测试资源排序器。"""
    
    def test_rank_resources(self):
        """测试资源排序。"""
        ranker = ResourceRanker()
        
        resources = [
            {
                "title": "高质量资源",
                "url": "https://example.com/1",
                "type": "article",
                "description": "详细内容" * 100,
                "metadata": {"play_count": 100000}
            },
            {
                "title": "低质量资源",
                "url": "https://example.com/2",
                "type": "article",
                "description": "简短",
                "metadata": {}
            },
        ]
        
        ranked = ranker.rank(resources)
        
        assert len(ranked) == 2
        # 高质量资源应该排在前面
        assert ranked[0].title == "高质量资源"
        assert ranked[0].quality_score > ranked[1].quality_score
    
    def test_rank_with_deduplication(self):
        """测试带去重的排序。"""
        ranker = ResourceRanker()
        
        resources = [
            {"title": "资源 1", "url": "https://example.com/1", "type": "article"},
            {"title": "资源 2", "url": "https://example.com/2", "type": "article"},
            {"title": "资源 1 重复", "url": "https://example.com/1", "type": "article"},
        ]
        
        ranked = ranker.rank(resources, deduplicate=True)
        
        assert len(ranked) == 2
    
    def test_rank_custom_weights(self):
        """测试自定义权重排序。"""
        ranker = ResourceRanker()
        
        resources = [
            {
                "title": "新资源",
                "url": "https://example.com/1",
                "type": "article",
                "publish_date": datetime.now(),
                "description": "内容"
            },
            {
                "title": "旧资源",
                "url": "https://example.com/2",
                "type": "article",
                "publish_date": datetime.now() - timedelta(days=365),
                "description": "内容"
            },
        ]
        
        # 强调时效性
        weights = {"content_quality": 0.1, "authority": 0.1, "freshness": 0.6, "engagement": 0.1, "completeness": 0.1}
        ranked = ranker.rank(resources, weights=weights)
        
        # 新资源应该排在前面
        assert ranked[0].title == "新资源"


class TestResourceRankerService:
    """测试资源评分服务。"""
    
    def test_rank_resources_service(self):
        """测试服务排序。"""
        service = ResourceRankerService()
        
        resources = [
            {"title": f"资源{i}", "url": f"https://example.com/{i}", "type": "article", "description": "内容" * 10}
            for i in range(10)
        ]
        
        ranked = service.rank_resources(resources, top_n=5)
        
        assert len(ranked) == 5
        assert all(isinstance(r, RankedResource) for r in ranked)
    
    def test_get_recommendations_default(self):
        """测试默认推荐。"""
        service = ResourceRankerService()
        
        resources = [
            {"title": "资源", "url": "https://example.com", "type": "article", "description": "内容"}
        ]
        
        recommendations = service.get_recommendations(resources, top_n=1)
        
        assert len(recommendations) == 1
    
    def test_get_recommendations_fresh(self):
        """测试偏好新鲜的推荐。"""
        service = ResourceRankerService()
        
        resources = [
            {
                "title": "新资源",
                "url": "https://example.com/1",
                "type": "article",
                "publish_date": datetime.now(),
                "description": "内容"
            },
            {
                "title": "旧资源",
                "url": "https://example.com/2",
                "type": "article",
                "publish_date": datetime.now() - timedelta(days=365),
                "description": "内容"
            },
        ]
        
        preferences = {"prefer_fresh": True}
        recommendations = service.get_recommendations(resources, preferences, top_n=2)
        
        assert recommendations[0].title == "新资源"
    
    def test_get_recommendations_authoritative(self):
        """测试偏好权威的推荐。"""
        service = ResourceRankerService()
        
        resources = [
            {
                "title": "权威资源",
                "url": "https://www.youtube.com/watch?v=xxx",
                "type": "youtube_video",
                "description": "内容"
            },
            {
                "title": "普通资源",
                "url": "https://unknown-blog.com/post",
                "type": "article",
                "description": "内容"
            },
        ]
        
        preferences = {"prefer_authoritative": True}
        recommendations = service.get_recommendations(resources, preferences, top_n=2)
        
        # YouTube 应该排在前面
        assert recommendations[0].title == "权威资源"


class TestRankedResource:
    """测试 RankedResource 数据类。"""
    
    def test_ranked_resource_creation(self):
        """测试排序资源创建。"""
        from edict.backend.app.services.resource_ranker import QualityMetrics
        
        resource = RankedResource(
            id="res_001",
            title="测试资源",
            url="https://example.com",
            resource_type="article",
            quality_score=0.85,
            quality_tier=ResourceQualityTier.GOOD,
            metrics=QualityMetrics()
        )
        
        assert resource.id == "res_001"
        assert resource.quality_score == 0.85
        assert resource.quality_tier == ResourceQualityTier.GOOD
    
    def test_ranked_resource_to_dict(self):
        """测试排序资源转字典。"""
        from edict.backend.app.services.resource_ranker import QualityMetrics
        
        resource = RankedResource(
            id="res_001",
            title="测试",
            url="https://example.com",
            resource_type="article",
            quality_score=0.8,
            quality_tier=ResourceQualityTier.GOOD,
            metrics=QualityMetrics(),
            publish_date=datetime(2024, 1, 1)
        )
        
        data = resource.to_dict()
        
        assert data["id"] == "res_001"
        assert data["quality_tier"] == "good"
        assert "metrics" in data


class TestQualityTier:
    """测试质量分级。"""
    
    def test_tier_values(self):
        """测试分级值。"""
        assert ResourceQualityTier.EXCELLENT.value == "excellent"
        assert ResourceQualityTier.GOOD.value == "good"
        assert ResourceQualityTier.FAIR.value == "fair"
        assert ResourceQualityTier.POOR.value == "poor"


class TestConvenienceFunctions:
    """测试便捷函数。"""
    
    def test_rank_resources_function(self):
        """测试排序便捷函数。"""
        resources = [
            {"title": "资源", "url": "https://example.com", "type": "article", "description": "内容"}
        ]
        
        ranked = rank_resources(resources, top_n=1)
        
        assert len(ranked) == 1
        assert isinstance(ranked[0], RankedResource)
    
    def test_get_recommendations_function(self):
        """测试推荐便捷函数。"""
        resources = [
            {"title": "资源", "url": "https://example.com", "type": "article", "description": "内容"}
        ]
        
        recommendations = get_recommendations(resources, top_n=1)
        
        assert len(recommendations) == 1


class TestIntegration:
    """集成测试。"""
    
    def test_full_ranking_workflow(self):
        """测试完整排序流程。"""
        service = ResourceRankerService()
        
        # 创建混合质量资源
        resources = [
            {
                "title": "优质教程：Python 从入门到精通",
                "url": "https://www.bilibili.com/video/python",
                "type": "bilibili_video",
                "description": "详细内容" * 100,
                "author": "知名 UP 主",
                "publish_date": datetime.now() - timedelta(days=10),
                "duration": 1800,
                "metadata": {"play_count": 500000, "favorites": 20000, "danmaku": 5000}
            },
            {
                "title": "简单教程",
                "url": "https://blog.example.com/simple",
                "type": "article",
                "description": "简短描述",
                "publish_date": datetime.now() - timedelta(days=300),
                "metadata": {}
            },
            {
                "title": "震惊！100% 必学",
                "url": "https://clickbait.com/article",
                "type": "article",
                "description": "标题党内容",
                "metadata": {"play_count": 100}
            },
        ]
        
        # 排序
        ranked = service.rank_resources(resources)
        
        assert len(ranked) == 3
        
        # 优质资源应该排第一
        assert ranked[0].title == "优质教程：Python 从入门到精通"
        assert ranked[0].quality_tier in [ResourceQualityTier.EXCELLENT, ResourceQualityTier.GOOD]
        
        # 标题党应该排最后
        assert ranked[-1].quality_score < ranked[0].quality_score
    
    def test_batch_processing(self):
        """测试批量处理。"""
        service = ResourceRankerService()
        
        # 创建大量资源
        resources = [
            {
                "title": f"资源{i}",
                "url": f"https://example.com/{i}",
                "type": "article",
                "description": "内容" * 10,
                "metadata": {"play_count": i * 100}
            }
            for i in range(50)
        ]
        
        ranked = service.rank_resources(resources, top_n=10)
        
        assert len(ranked) == 10
        # 应该按质量降序排列
        for i in range(len(ranked) - 1):
            assert ranked[i].quality_score >= ranked[i + 1].quality_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
