"""OCR 解析服务测试。

测试覆盖：
1. 中文 OCR 识别
2. 英文 OCR 识别
3. 混合排版支持
4. 表格结构识别
5. PDF 解析
6. 集成测试
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from PIL import Image
import numpy as np

from edict.backend.app.services.ocr_parser import (
    OCRParserService,
    PaddleOCREngine,
    TableStructureRecognizer,
    LanguageDetector,
    OCRResult,
    TextBlock,
    TableBlock,
    TextDirection,
    parse_image_ocr,
    parse_pdf_ocr,
    image_to_markdown,
    pdf_to_markdown,
)


class TestTextBlock:
    """测试 TextBlock 数据类。"""
    
    def test_text_block_creation(self):
        """测试文字块创建。"""
        block = TextBlock(
            text="测试文字",
            confidence=0.95,
            bbox=(10, 20, 100, 50),
            language="zh",
            direction=TextDirection.HORIZONTAL
        )
        
        assert block.text == "测试文字"
        assert block.confidence == 0.95
        assert block.bbox == (10, 20, 100, 50)
        assert block.language == "zh"
    
    def test_text_block_to_dict(self):
        """测试文字块转字典。"""
        block = TextBlock(
            text="测试",
            confidence=0.9,
            bbox=(0, 0, 100, 100),
            block_type="text"
        )
        
        data = block.to_dict()
        
        assert data["text"] == "测试"
        assert data["confidence"] == 0.9
        assert data["bbox"] == (0, 0, 100, 100)
        assert data["direction"] == "horizontal"


class TestTableBlock:
    """测试 TableBlock 数据类。"""
    
    def test_table_block_creation(self):
        """测试表格块创建。"""
        rows = [
            ["姓名", "年龄", "城市"],
            ["张三", "25", "北京"],
            ["李四", "30", "上海"]
        ]
        
        table = TableBlock(
            rows=rows,
            bbox=(10, 10, 200, 100),
            has_header=True
        )
        
        assert len(table.rows) == 3
        assert table.has_header is True
    
    def test_table_to_markdown(self):
        """测试表格转 Markdown。"""
        rows = [
            ["姓名", "年龄"],
            ["张三", "25"],
            ["李四", "30"]
        ]
        
        table = TableBlock(rows=rows, bbox=(0, 0, 100, 100))
        markdown = table.to_markdown()
        
        assert "| 姓名 | 年龄 |" in markdown
        assert "| --- | --- |" in markdown
        assert "| 张三 | 25 |" in markdown
    
    def test_table_to_dict(self):
        """测试表格转字典。"""
        rows = [["标题", "内容"]]
        table = TableBlock(rows=rows, bbox=(0, 0, 100, 100))
        
        data = table.to_dict()
        
        assert "rows" in data
        assert "markdown" in data
        assert data["bbox"] == (0, 0, 100, 100)


class TestOCRResult:
    """测试 OCRResult 数据类。"""
    
    def test_ocr_result_creation(self):
        """测试 OCR 结果创建。"""
        result = OCRResult(
            success=True,
            text_blocks=[],
            table_blocks=[],
            full_text="测试文本",
            markdown="# 测试",
            page=1
        )
        
        assert result.success is True
        assert result.full_text == "测试文本"
        assert result.page == 1
    
    def test_ocr_result_to_dict(self):
        """测试 OCR 结果转字典。"""
        result = OCRResult(
            success=True,
            text_blocks=[TextBlock(text="测试", confidence=0.9, bbox=(0, 0, 100, 100))],
            table_blocks=[],
            full_text="测试",
            markdown="测试",
            page=1
        )
        
        data = result.to_dict()
        
        assert data["success"] is True
        assert len(data["text_blocks"]) == 1
        assert data["full_text"] == "测试"


class TestLanguageDetector:
    """测试语言检测器。"""
    
    def test_detect_chinese(self):
        """测试中文检测。"""
        detector = LanguageDetector()
        
        assert detector.detect("这是一个中文句子") == "zh"
        assert detector.detect("你好世界") == "zh"
    
    def test_detect_english(self):
        """测试英文检测。"""
        detector = LanguageDetector()
        
        assert detector.detect("This is an English sentence") == "en"
        assert detector.detect("Hello World") == "en"
    
    def test_detect_mixed(self):
        """测试混合语言检测。"""
        detector = LanguageDetector()
        
        assert detector.detect("Hello 世界") == "mixed"
        assert detector.detect("Python 编程教程") == "mixed"
    
    def test_detect_empty(self):
        """测试空文本检测。"""
        detector = LanguageDetector()
        
        assert detector.detect("") == "unknown"
        assert detector.detect(None) == "unknown"


class TestPaddleOCREngine:
    """测试 PaddleOCR 引擎。"""
    
    def test_initialization(self):
        """测试引擎初始化。"""
        engine = PaddleOCREngine(use_gpu=False, lang="ch")
        
        assert engine.use_gpu is False
        assert engine.lang == "ch"
        assert engine._ocr is None  # 延迟加载
    
    def test_recognize_file_not_found(self):
        """测试文件不存在的识别。"""
        engine = PaddleOCREngine()
        
        # 不实际调用 PaddleOCR，只测试错误处理
        with patch.object(engine, '_get_ocr') as mock_get_ocr:
            mock_get_ocr.side_effect = Exception("PaddleOCR not installed")
            
            results, info = engine.recognize(Path("/nonexistent/file.png"))
            
            assert results == []
            assert "error" in info
    
    def test_recognize_mock(self):
        """测试识别（Mock）。"""
        engine = PaddleOCREngine()
        
        # Mock PaddleOCR 结果
        mock_ocr = MagicMock()
        mock_ocr.ocr.return_value = [[
            [[[10, 10], [100, 10], [100, 50], [10, 50]], ("测试文字", 0.95)]
        ]]
        
        with patch.object(engine, '_get_ocr', return_value=mock_ocr):
            results, info = engine.recognize(Path("/fake/image.png"))
            
            assert len(results) == 1
            assert results[0]["text"] == "测试文字"
            assert results[0]["confidence"] == 0.95
            assert results[0]["bbox"] == (10, 10, 100, 50)


class TestTableStructureRecognizer:
    """测试表格结构识别器。"""
    
    def test_initialization(self):
        """测试初始化。"""
        recognizer = TableStructureRecognizer()
        
        assert recognizer._table_engine is None  # 延迟加载
    
    def test_fallback_table_recognition(self):
        """测试备用表格识别。"""
        recognizer = TableStructureRecognizer()
        
        # 创建测试图片
        test_img = Image.new('RGB', (200, 200), color='white')
        test_path = Path("/tmp/test_table.png")
        
        # Mock PIL 和 cv2
        with patch('PIL.Image.open', return_value=test_img):
            with patch('edict.backend.app.services.ocr_parser.cv2') as mock_cv2:
                mock_cv2.Canny.return_value = np.zeros((200, 200))
                mock_cv2.countNonZero.return_value = 0  # 无表格线
                
                result = recognizer._fallback_table_recognition(test_path, (0, 0, 200, 200))
                
                # 无表格线应返回 None
                assert result is None


class TestOCRParserService:
    """测试 OCR 解析服务。"""
    
    def test_service_initialization(self):
        """测试服务初始化。"""
        service = OCRParserService(use_gpu=False)
        
        assert service.ocr_engine is not None
        assert service.table_recognizer is not None
        assert service.language_detector is not None
    
    def test_parse_image_not_found(self):
        """测试图片不存在的解析。"""
        service = OCRParserService()
        
        result = service.parse_image(Path("/nonexistent/image.png"))
        
        assert result.success is False
        assert "文件不存在" in result.error
    
    def test_parse_image_mock(self):
        """测试图片解析（Mock）。"""
        service = OCRParserService()
        
        # Mock OCR 引擎
        with patch.object(service.ocr_engine, 'recognize') as mock_recognize:
            mock_recognize.return_value = ([
                {"text": "第一行", "confidence": 0.95, "bbox": (10, 10, 100, 30)},
                {"text": "第二行", "confidence": 0.90, "bbox": (10, 40, 100, 60)},
            ], {})
            
            # Mock 图片尺寸获取
            with patch.object(service, '_get_image_size', return_value={"width": 800, "height": 600}):
                result = service.parse_image(Path("/fake/image.png"))
                
                assert result.success is True
                assert len(result.text_blocks) == 2
                assert "第一行" in result.full_text
                assert "第二行" in result.full_text
    
    def test_parse_pdf_not_found(self):
        """测试 PDF 不存在的解析。"""
        service = OCRParserService()
        
        results = service.parse_pdf(Path("/nonexistent/file.pdf"))
        
        assert len(results) == 1
        assert results[0].success is False
        assert "文件不存在" in results[0].error
    
    def test_parse_pdf_no_pymupdf(self):
        """测试无 PyMuPDF 时的 PDF 解析。"""
        service = OCRParserService()
        
        with patch.dict('sys.modules', {'fitz': None}):
            results = service.parse_pdf(Path("/fake/file.pdf"))
            
            assert len(results) == 1
            assert results[0].success is False
            assert "PyMuPDF" in results[0].error


class TestConvenienceFunctions:
    """测试便捷函数。"""
    
    def test_parse_image_ocr(self):
        """测试图片 OCR 便捷函数。"""
        with patch('edict.backend.app.services.ocr_parser.OCRParserService') as MockService:
            mock_service = MockService.return_value
            mock_service.parse_image.return_value = OCRResult(
                success=True,
                text_blocks=[],
                table_blocks=[],
                full_text="测试",
                markdown="测试",
                page=1
            )
            
            result = parse_image_ocr("/fake/image.png")
            
            assert result.success is True
            assert result.full_text == "测试"
    
    def test_image_to_markdown(self):
        """测试图片转 Markdown 便捷函数。"""
        with patch('edict.backend.app.services.ocr_parser.parse_image_ocr') as mock_parse:
            mock_parse.return_value = OCRResult(
                success=True,
                text_blocks=[],
                table_blocks=[],
                full_text="测试",
                markdown="# 测试标题",
                page=1
            )
            
            markdown = image_to_markdown("/fake/image.png")
            
            assert markdown == "# 测试标题"
    
    def test_image_to_markdown_failure(self):
        """测试图片转 Markdown 失败情况。"""
        with patch('edict.backend.app.services.ocr_parser.parse_image_ocr') as mock_parse:
            mock_parse.return_value = OCRResult(
                success=False,
                text_blocks=[],
                table_blocks=[],
                full_text="",
                markdown="",
                page=0,
                error="OCR 失败"
            )
            
            markdown = image_to_markdown("/fake/image.png")
            
            assert markdown == ""


class TestIntegration:
    """集成测试。"""
    
    def test_full_ocr_workflow(self):
        """测试完整 OCR 工作流程。"""
        service = OCRParserService()
        
        # Mock OCR 引擎返回多语言文本
        with patch.object(service.ocr_engine, 'recognize') as mock_recognize:
            mock_recognize.return_value = ([
                {"text": "中文文本", "confidence": 0.95, "bbox": (10, 10, 100, 30)},
                {"text": "English text", "confidence": 0.90, "bbox": (10, 40, 100, 60)},
                {"text": "混合 Mixed", "confidence": 0.85, "bbox": (10, 70, 100, 90)},
            ], {})
            
            with patch.object(service, '_get_image_size', return_value={}):
                result = service.parse_image(Path("/fake/image.png"))
                
                assert result.success is True
                assert len(result.text_blocks) == 3
                
                # 检查语言检测
                assert result.text_blocks[0].language == "zh"
                assert result.text_blocks[1].language == "en"
                assert result.text_blocks[2].language == "mixed"
                
                # 检查 Markdown 生成
                assert "中文文本" in result.markdown
                assert "English text" in result.markdown
    
    def test_table_detection_integration(self):
        """测试表格检测集成。"""
        service = OCRParserService()
        
        # Mock 大量文本块（可能包含表格）
        with patch.object(service.ocr_engine, 'recognize') as mock_recognize:
            # 生成 15 个文本块模拟表格区域
            mock_data = [
                {"text": f"单元格{i}", "confidence": 0.9, "bbox": (10 + i*20, 10, 30 + i*20, 30)}
                for i in range(15)
            ]
            mock_recognize.return_value = (mock_data, {})
            
            with patch.object(service, '_get_image_size', return_value={}):
                result = service.parse_image(Path("/fake/table.png"))
                
                assert result.success is True
                assert len(result.text_blocks) == 15
                # 表格检测可能识别出表格（取决于实现）
                assert isinstance(result.table_blocks, list)


class TestEdgeCases:
    """边界情况测试。"""
    
    def test_empty_image(self):
        """测试空白图片。"""
        service = OCRParserService()
        
        with patch.object(service.ocr_engine, 'recognize') as mock_recognize:
            mock_recognize.return_value = ([], {})
            
            with patch.object(service, '_get_image_size', return_value={}):
                result = service.parse_image(Path("/fake/empty.png"))
                
                assert result.success is True
                assert len(result.text_blocks) == 0
                assert result.full_text == ""
    
    def test_low_confidence_text(self):
        """测试低置信度文本。"""
        service = OCRParserService()
        
        with patch.object(service.ocr_engine, 'recognize') as mock_recognize:
            mock_recognize.return_value = ([
                {"text": "模糊文字", "confidence": 0.3, "bbox": (10, 10, 100, 30)},
            ], {})
            
            with patch.object(service, '_get_image_size', return_value={}):
                result = service.parse_image(Path("/fake/blurry.png"))
                
                assert result.success is True
                assert result.text_blocks[0].confidence == 0.3
    
    def test_very_long_text(self):
        """测试超长文本。"""
        service = OCRParserService()
        
        long_text = "测试" * 1000
        
        with patch.object(service.ocr_engine, 'recognize') as mock_recognize:
            mock_recognize.return_value = ([
                {"text": long_text, "confidence": 0.95, "bbox": (10, 10, 500, 100)},
            ], {})
            
            with patch.object(service, '_get_image_size', return_value={}):
                result = service.parse_image(Path("/fake/long.png"))
                
                assert result.success is True
                assert len(result.full_text) > 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
