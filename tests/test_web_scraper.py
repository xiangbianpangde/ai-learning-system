"""网页抓取服务测试。

测试覆盖：
1. B 站搜索 API
2. YouTube Data API
3. 通用网页内容提取
4. 资源去重
5. 集成测试
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from datetime import datetime

from edict.backend.app.services.web_scraper import (
    WebScraperService,
    BilibiliSearchAPI,
    YouTubeSearchAPI,
    WebContentExtractor,
    ResourceDeduplicator,
    Resource,
    ResourceType,
    search_resources_sync,
    extract_webpage_sync,
)


class TestResource:
    """测试 Resource 数据类。"""
    
    def test_resource_creation(self):
        """测试资源创建。"""
        resource = Resource(
            title="测试视频",
            url="https://example.com/video",
            resource_type=ResourceType.VIDEO_BILIBILI,
            duration=600,
            description="测试描述",
            author="测试作者"
        )
        
        assert resource.title == "测试视频"
        assert resource.url == "https://example.com/video"
        assert resource.resource_type == ResourceType.VIDEO_BILIBILI
        assert resource.duration == 600
    
    def test_resource_to_dict(self):
        """测试资源转字典。"""
        resource = Resource(
            title="测试",
            url="https://example.com",
            resource_type=ResourceType.ARTICLE,
            publish_date=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        data = resource.to_dict()
        
        assert data["title"] == "测试"
        assert data["url"] == "https://example.com"
        assert data["type"] == "article"
        assert data["publish_date"] == "2024-01-01T12:00:00"


class TestBilibiliSearchAPI:
    """测试 B 站搜索 API。"""
    
    def test_parse_duration_standard(self):
        """测试标准时长解析。"""
        api = BilibiliSearchAPI()
        
        assert api._parse_duration("10:30") == 630
        assert api._parse_duration("1:30:45") == 5445
        assert api._parse_duration("0:00") == 0
    
    def test_parse_duration_invalid(self):
        """测试无效时长解析。"""
        api = BilibiliSearchAPI()
        
        assert api._parse_duration("invalid") == 0
        assert api._parse_duration("") == 0
    
    def test_calculate_bilibili_score(self):
        """测试 B 站评分计算。"""
        api = BilibiliSearchAPI()
        
        # 高播放量视频
        item1 = {"play": 1000000, "video_review": 10000, "favorites": 50000}
        score1 = api._calculate_bilibili_score(item1)
        assert 0.0 <= score1 <= 1.0
        
        # 低播放量视频
        item2 = {"play": 100, "video_review": 0, "favorites": 0}
        score2 = api._calculate_bilibili_score(item2)
        assert score2 < score1
    
    @pytest.mark.asyncio
    async def test_search_mock(self):
        """测试搜索（Mock API）。"""
        api = BilibiliSearchAPI()
        
        # Mock HTTP 响应
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "result": [
                    {
                        "title": "测试视频",
                        "bvid": "BV1234567890",
                        "duration": "10:30",
                        "author": "测试 UP 主",
                        "description": "测试描述",
                        "play": 100000,
                        "video_review": 1000,
                        "favorites": 5000
                    }
                ]
            }
        }
        
        with patch.object(api.session, 'get', return_value=mock_response):
            resources = await api.search("测试关键词")
            
            assert len(resources) == 1
            assert resources[0].title == "测试视频"
            assert resources[0].resource_type == ResourceType.VIDEO_BILIBILI
        
        await api.close()


class TestYouTubeSearchAPI:
    """测试 YouTube 搜索 API。"""
    
    def test_parse_iso_duration(self):
        """测试 ISO 8601 时长解析。"""
        api = YouTubeSearchAPI()
        
        assert api._parse_iso_duration("PT10M30S") == 630
        assert api._parse_iso_duration("PT1H30M45S") == 5445
        assert api._parse_iso_duration("PT45S") == 45
        assert api._parse_iso_duration("PT2H") == 7200
    
    def test_calculate_youtube_score(self):
        """测试 YouTube 评分计算。"""
        api = YouTubeSearchAPI()
        
        item = {"snippet": {"title": "测试"}}
        score = api._calculate_youtube_score(item)
        
        assert 0.0 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_search_no_api_key(self):
        """测试无 API Key 时的搜索。"""
        api = YouTubeSearchAPI(api_key=None)
        
        with patch.dict('os.environ', {}, clear=True):
            resources = await api.search("测试")
            
            assert resources == []
        
        await api.close()


class TestWebContentExtractor:
    """测试网页内容提取器。"""
    
    def test_extract_with_regex(self):
        """测试正则表达式提取。"""
        extractor = WebContentExtractor()
        
        html = """
        <html>
            <head><title>测试页面</title></head>
            <body>
                <script>alert('test');</script>
                <p>这是测试内容</p>
                <style>.test { color: red; }</style>
            </body>
        </html>
        """
        
        text = extractor._extract_with_regex(html)
        
        assert "测试内容" in text
        assert "alert" not in text  # script 应被移除
        assert ".test" not in text  # style 应被移除
    
    def test_extract_title(self):
        """测试标题提取。"""
        extractor = WebContentExtractor()
        
        html = "<html><head><title>测试页面标题</title></head></html>"
        title = extractor._extract_title(html)
        
        assert title == "测试页面标题"
    
    def test_detect_resource_type(self):
        """测试资源类型检测。"""
        extractor = WebContentExtractor()
        
        # 博客
        assert extractor._detect_resource_type("https://medium.com/blog", "").value == "blog"
        
        # 文档
        assert extractor._detect_resource_type("https://docs.python.org", "").value == "documentation"
        
        # 普通文章
        assert extractor._detect_resource_type("https://example.com/article", "").value == "article"
    
    def test_calculate_web_score(self):
        """测试网页质量评分。"""
        extractor = WebContentExtractor()
        
        # 高质量网页
        html_good = "<html><h1>标题</h1><p>" + "内容" * 500 + "<code>代码</code></p></html>"
        score_good = extractor._calculate_web_score("内容" * 500, html_good)
        
        # 低质量网页
        html_bad = "<html><p>短内容</p></html>"
        score_bad = extractor._calculate_web_score("短内容", html_bad)
        
        assert score_good > score_bad


class TestResourceDeduplicator:
    """测试资源去重器。"""
    
    def test_deduplicate_by_url(self):
        """测试基于 URL 的去重。"""
        deduplicator = ResourceDeduplicator()
        
        resources = [
            Resource(title="资源 1", url="https://example.com/1", resource_type=ResourceType.ARTICLE),
            Resource(title="资源 2", url="https://example.com/2", resource_type=ResourceType.ARTICLE),
            Resource(title="资源 1 重复", url="https://example.com/1", resource_type=ResourceType.ARTICLE),
        ]
        
        unique = deduplicator.deduplicate(resources)
        
        assert len(unique) == 2
        assert all(r.url in ["https://example.com/1", "https://example.com/2"] for r in unique)
    
    def test_reset(self):
        """测试重置去重状态。"""
        deduplicator = ResourceDeduplicator()
        
        resources = [
            Resource(title="资源", url="https://example.com", resource_type=ResourceType.ARTICLE),
        ]
        
        deduplicator.deduplicate(resources)
        assert len(deduplicator.seen_hashes) == 1
        
        deduplicator.reset()
        assert len(deduplicator.seen_hashes) == 0


class TestWebScraperService:
    """测试网页抓取服务。"""
    
    @pytest.mark.asyncio
    async def test_search_integration(self):
        """测试集成搜索（Mock）。"""
        service = WebScraperService()
        
        # Mock B 站 API
        mock_bilibili = AsyncMock()
        mock_bilibili.search.return_value = [
            Resource(title="B 站视频", url="https://bilibili.com/video/1", resource_type=ResourceType.VIDEO_BILIBILI)
        ]
        service.bilibili_api = mock_bilibili
        
        # Mock YouTube API
        mock_youtube = AsyncMock()
        mock_youtube.search.return_value = []
        service.youtube_api = mock_youtube
        
        resources = await service.search("测试关键词", sources=["bilibili"])
        
        assert len(resources) == 1
        assert resources[0].title == "B 站视频"
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_extract_from_url(self):
        """测试 URL 提取（Mock）。"""
        service = WebScraperService()
        
        mock_extractor = AsyncMock()
        mock_extractor.extract.return_value = Resource(
            title="提取的网页",
            url="https://example.com",
            resource_type=ResourceType.ARTICLE
        )
        service.web_extractor = mock_extractor
        
        resource = await service.extract_from_url("https://example.com")
        
        assert resource is not None
        assert resource.title == "提取的网页"
        
        await service.close()


class TestConvenienceFunctions:
    """测试便捷函数。"""
    
    def test_search_resources_sync(self):
        """测试同步搜索函数（Mock）。"""
        with patch('edict.backend.app.services.web_scraper.WebScraperService') as MockService:
            mock_service = MockService.return_value
            mock_service.search = AsyncMock(return_value=[])
            
            resources = search_resources_sync("测试")
            
            assert resources == []
            mock_service.search.assert_called_once()
            mock_service.close.assert_called_once()
    
    def test_extract_webpage_sync(self):
        """测试同步网页提取函数（Mock）。"""
        with patch('edict.backend.app.services.web_scraper.WebScraperService') as MockService:
            mock_service = MockService.return_value
            mock_service.extract_from_url = AsyncMock(return_value=None)
            
            result = extract_webpage_sync("https://example.com")
            
            assert result is None


class TestIntegration:
    """集成测试。"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程。"""
        service = WebScraperService()
        
        # Mock 所有 API
        mock_bilibili = AsyncMock()
        mock_bilibili.search.return_value = [
            Resource(
                title="Python 教程",
                url="https://bilibili.com/video/python",
                resource_type=ResourceType.VIDEO_BILIBILI,
                duration=1800,
                author="教程 UP 主",
                metadata={"play": 500000}
            )
        ]
        service.bilibili_api = mock_bilibili
        
        mock_youtube = AsyncMock()
        mock_youtube.search.return_value = []
        service.youtube_api = mock_youtube
        
        # 搜索
        resources = await service.search("Python 教程", sources=["bilibili"])
        
        assert len(resources) == 1
        assert resources[0].title == "Python 教程"
        assert resources[0].duration == 1800
        
        # 去重（应该没有变化）
        unique = service.deduplicator.deduplicate(resources)
        assert len(unique) == 1
        
        await service.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
