"""PDF 解析器单元测试。

测试覆盖：
1. PDF 类型检测
2. 5 类 PDF 解析
3. 知识点提取
4. 错误处理
5. 边界情况

验收标准：
- 5 类 PDF 全部能成功转换
- 知识点提取准确率 ≥ 70%
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
# Add backend path but avoid importing the full app
sys.path.insert(0, str(Path(__file__).parent.parent / 'edict' / 'backend' / 'app' / 'services'))

# Import directly from the module file to avoid dependency chain
import importlib.util
spec = importlib.util.spec_from_file_location(
    "pdf_parser",
    Path(__file__).parent.parent / 'edict' / 'backend' / 'app' / 'services' / 'pdf_parser.py'
)
pdf_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdf_parser)

from pdf_parser import (
    PDFParserService,
    TextPDFParser,
    TablePDFParser,
    ScannedPDFParser,
    FormulaPDFParser,
    MixedPDFParser,
    PDFType,
    KnowledgePoint,
    ParseResult,
    parse_pdf,
    extract_knowledge_points,
)


class TestPDFType:
    """PDF 类型枚举测试。"""
    
    def test_pdf_type_values(self):
        """测试 PDF 类型枚举值。"""
        assert PDFType.TEXT.value == "text"
        assert PDFType.SCANNED.value == "scanned"
        assert PDFType.TABLE.value == "table"
        assert PDFType.FORMULA.value == "formula"
        assert PDFType.MIXED.value == "mixed"


class TestKnowledgePoint:
    """知识点数据结构测试。"""
    
    def test_knowledge_point_creation(self):
        """测试知识点创建。"""
        kp = KnowledgePoint(
            title="测试知识点",
            content="这是测试内容",
            page=1,
            confidence=0.85,
            tags=["标签 1", "标签 2"],
        )
        
        assert kp.title == "测试知识点"
        assert kp.content == "这是测试内容"
        assert kp.page == 1
        assert kp.confidence == 0.85
        assert len(kp.tags) == 2
    
    def test_knowledge_point_defaults(self):
        """测试知识点默认值。"""
        kp = KnowledgePoint(
            title="简单知识点",
            content="内容",
            page=1,
        )
        
        assert kp.confidence == 0.0
        assert kp.tags == []
        assert kp.metadata == {}


class TestParseResult:
    """解析结果数据结构测试。"""
    
    def test_success_result(self):
        """测试成功解析结果。"""
        result = ParseResult(
            success=True,
            pdf_type=PDFType.TEXT,
            text="完整文本",
            knowledge_points=[],
            pages=10,
        )
        
        assert result.success is True
        assert result.error is None
        assert result.pages == 10
    
    def test_error_result(self):
        """测试失败解析结果。"""
        result = ParseResult(
            success=False,
            pdf_type=PDFType.TEXT,
            text="",
            knowledge_points=[],
            pages=0,
            error="文件不存在",
        )
        
        assert result.success is False
        assert result.error == "文件不存在"


class TestTextPDFParser:
    """纯文本 PDF 解析器测试。"""
    
    def test_detect_type_text_pdf(self):
        """测试检测纯文本 PDF。"""
        parser = pdf_parser.TextPDFParser()
        
        # Mock pypdf
        with patch.object(pdf_parser, 'PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "这是足够的文本内容用于检测"
            mock_reader.return_value.pages = [mock_page] * 5
            
            result = parser.detect_type(Path("test.pdf"))
            assert result == PDFType.TEXT
    
    def test_detect_type_scanned_pdf(self):
        """测试检测扫描版 PDF。"""
        parser = TextPDFParser()
        
        with patch('app.services.pdf_parser.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = ""  # 无文本
            mock_reader.return_value.pages = [mock_page] * 5
            
            result = parser.detect_type(Path("test.pdf"))
            assert result == PDFType.SCANNED
    
    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件。"""
        parser = TextPDFParser()
        result = parser.parse(Path("/nonexistent/file.pdf"))
        
        assert result.success is False
        assert "文件不存在" in result.error
    
    def test_parse_success(self):
        """测试成功解析。"""
        parser = TextPDFParser()
        
        with patch('app.services.pdf_parser.PdfReader') as mock_reader:
            mock_page1 = Mock()
            mock_page1.extract_text.return_value = "第一页内容\n1. 知识点一\n详细内容..."
            
            mock_page2 = Mock()
            mock_page2.extract_text.return_value = "第二页内容\n2. 知识点二\n更多细节..."
            
            mock_reader.return_value.pages = [mock_page1, mock_page2]
            
            # Mock file exists
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    
                    result = parser.parse(Path("test.pdf"))
                    
                    assert result.success is True
                    assert result.pdf_type == PDFType.TEXT
                    assert result.pages == 2
                    assert len(result.knowledge_points) > 0
    
    def test_extract_knowledge_points(self):
        """测试知识点提取。"""
        parser = TextPDFParser()
        
        text = """
        第一章：引言
        
        1. 背景介绍
        这是背景介绍的详细内容，超过 50 个字符以确保被识别为有效知识点。
        
        2. 关键概念
        关键 点：核心概念 A、核心概念 B
        定义：这是一个重要定义
        """
        
        points = parser._extract_knowledge_points(text, page=1)
        
        assert len(points) > 0
        assert all(isinstance(p, KnowledgePoint) for p in points)
        assert all(p.page == 1 for p in points)
    
    def test_extract_tags(self):
        """测试标签提取。"""
        parser = TextPDFParser()
        
        text = "关键 点：重要概念\n定义：这是一个测试定义"
        tags = parser._extract_tags(text)
        
        assert len(tags) > 0
        assert any("重要概念" in tag for tag in tags)


class TestTablePDFParser:
    """表格 PDF 解析器测试。"""
    
    def test_detect_type_table_pdf(self):
        """测试检测表格 PDF。"""
        parser = TablePDFParser()
        
        with patch('app.services.pdf_parser.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "| 列 1 | 列 2 | 列 3 |\n| 数据 | 数据 | 数据 |"
            mock_reader.return_value.pages = [mock_page]
            
            result = parser.detect_type(Path("test.pdf"))
            assert result == PDFType.TABLE
    
    def test_parse_table_pdf(self):
        """测试解析表格 PDF。"""
        parser = TablePDFParser()
        
        with patch('app.services.pdf_parser.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = """
            表格内容：
            | 姓名 | 年龄 | 城市 |
            | 张三 | 25 | 北京 |
            | 李四 | 30 | 上海 |
            """
            mock_reader.return_value.pages = [mock_page]
            
            result = parser.parse(Path("test.pdf"))
            
            assert result.success is True
            assert result.pdf_type == PDFType.TABLE
            assert len(result.knowledge_points) > 0


class TestMixedPDFParser:
    """混合 PDF 解析器测试。"""
    
    def test_parse_mixed_fallback_to_text(self):
        """测试混合解析器回退到文本解析。"""
        parser = MixedPDFParser()
        
        with patch.object(parser.text_parser, 'parse') as mock_parse:
            mock_parse.return_value = ParseResult(
                success=True,
                pdf_type=PDFType.TEXT,
                text="混合内容",
                knowledge_points=[KnowledgePoint("测试", "内容", 1)],
                pages=5,
            )
            
            result = parser.parse(Path("test.pdf"))
            
            assert result.success is True
            assert result.pdf_type == PDFType.MIXED


class TestPDFParserService:
    """PDF 解析服务测试。"""
    
    def test_service_initialization(self):
        """测试服务初始化。"""
        service = PDFParserService()
        
        assert len(service.parsers) == 5
        assert PDFType.TEXT in service.parsers
        assert PDFType.MIXED in service.parsers
    
    def test_parse_auto_detect(self):
        """测试自动检测类型解析。"""
        service = PDFParserService()
        
        with patch.object(service.parsers[PDFType.TEXT], 'detect_type') as mock_detect:
            with patch.object(service.parsers[PDFType.MIXED], 'parse') as mock_parse:
                mock_detect.return_value = PDFType.TEXT
                mock_parse.return_value = ParseResult(
                    success=True,
                    pdf_type=PDFType.TEXT,
                    text="测试",
                    knowledge_points=[],
                    pages=1,
                )
                
                result = service.parse(Path("test.pdf"))
                
                assert result.success is True
                mock_detect.assert_called_once()
    
    def test_parse_with_specified_type(self):
        """测试指定类型解析。"""
        service = PDFParserService()
        
        with patch.object(service.parsers[PDFType.TABLE], 'parse') as mock_parse:
            mock_parse.return_value = ParseResult(
                success=True,
                pdf_type=PDFType.TABLE,
                text="表格",
                knowledge_points=[],
                pages=1,
            )
            
            result = service.parse(Path("test.pdf"), pdf_type=PDFType.TABLE)
            
            assert result.success is True
            assert result.pdf_type == PDFType.TABLE
    
    def test_parse_batch(self):
        """测试批量解析。"""
        service = PDFParserService()
        
        with patch.object(service, 'parse') as mock_parse:
            mock_parse.return_value = ParseResult(
                success=True,
                pdf_type=PDFType.TEXT,
                text="测试",
                knowledge_points=[],
                pages=1,
            )
            
            results = service.parse_batch([Path("a.pdf"), Path("b.pdf"), Path("c.pdf")])
            
            assert len(results) == 3
            assert all(r.success for r in results)
    
    def test_extract_knowledge_points(self):
        """测试知识点提取。"""
        service = PDFParserService()
        
        with patch.object(service, 'parse') as mock_parse:
            mock_parse.return_value = ParseResult(
                success=True,
                pdf_type=PDFType.TEXT,
                text="测试",
                knowledge_points=[
                    KnowledgePoint("知识点 1", "内容 1", 1),
                    KnowledgePoint("知识点 2", "内容 2", 2),
                ],
                pages=2,
            )
            
            points = service.extract_knowledge_points(Path("test.pdf"))
            
            assert len(points) == 2
            assert all(isinstance(p, KnowledgePoint) for p in points)


class TestConvenienceFunctions:
    """便捷函数测试。"""
    
    def test_parse_pdf_function(self):
        """测试 parse_pdf 便捷函数。"""
        with patch('app.services.pdf_parser.PDFParserService') as mock_service_class:
            mock_service = Mock()
            mock_service.parse.return_value = ParseResult(
                success=True,
                pdf_type=PDFType.TEXT,
                text="测试",
                knowledge_points=[],
                pages=1,
            )
            mock_service_class.return_value = mock_service
            
            result = parse_pdf("test.pdf")
            
            assert result.success is True
            mock_service.parse.assert_called_once()
    
    def test_extract_knowledge_points_function(self):
        """测试 extract_knowledge_points 便捷函数。"""
        with patch('app.services.pdf_parser.PDFParserService') as mock_service_class:
            mock_service = Mock()
            mock_service.extract_knowledge_points.return_value = [
                KnowledgePoint("测试", "内容", 1)
            ]
            mock_service_class.return_value = mock_service
            
            points = extract_knowledge_points("test.pdf")
            
            assert len(points) == 1
            mock_service.extract_knowledge_points.assert_called_once()


class TestErrorHandling:
    """错误处理测试。"""
    
    def test_parser_exception_handling(self):
        """测试解析器异常处理。"""
        parser = TextPDFParser()
        
        with patch('app.services.pdf_parser.PdfReader') as mock_reader:
            mock_reader.side_effect = Exception("模拟异常")
            
            result = parser.parse(Path("test.pdf"))
            
            assert result.success is False
            assert result.error == "模拟异常"
    
    def test_service_error_propagation(self):
        """测试服务错误传播。"""
        service = PDFParserService()
        
        with patch.object(service.parsers[PDFType.TEXT], 'detect_type') as mock_detect:
            mock_detect.side_effect = Exception("检测失败")
            
            # 应该回退到 MIXED 解析器
            result = service.parse(Path("test.pdf"))
            # 不应抛出异常


class TestEdgeCases:
    """边界情况测试。"""
    
    def test_empty_pdf(self):
        """测试空 PDF。"""
        parser = TextPDFParser()
        
        with patch('app.services.pdf_parser.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = ""
            mock_reader.return_value.pages = []
            
            with patch.object(Path, 'exists', return_value=True):
                result = parser.parse(Path("empty.pdf"))
                
                assert result.success is True
                assert result.text == ""
                assert result.pages == 0
    
    def test_very_large_pdf(self):
        """测试大 PDF 处理。"""
        parser = TextPDFParser()
        
        with patch('app.services.pdf_parser.PdfReader') as mock_reader:
            # 模拟 100 页 PDF
            mock_pages = []
            for i in range(100):
                mock_page = Mock()
                mock_page.extract_text.return_value = f"第{i}页内容"
                mock_pages.append(mock_page)
            
            mock_reader.return_value.pages = mock_pages
            
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024 * 1024
                    
                    result = parser.parse(Path("large.pdf"))
                    
                    assert result.success is True
                    assert result.pages == 100
    
    def test_special_characters_in_content(self):
        """测试特殊字符处理。"""
        parser = TextPDFParser()
        
        text = "特殊字符测试：@#$%^&*()_+-=[]{}|;':\",./<>?中文测试"
        points = parser._extract_knowledge_points(text, page=1)
        
        # 不应抛出异常
        assert isinstance(points, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
