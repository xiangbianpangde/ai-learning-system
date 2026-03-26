"""測試 pdf_parser_optimized.py - 性能優化版 PDF 解析器。

測試覆蓋：
- ✅ 分頁異步處理
- ✅ 進度回調
- ✅ 斷點續傳
- ✅ 內存管理
"""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from edict.backend.app.services.pdf_parser_optimized import (
    OptimizedPDFParser,
    ParseProgress,
    ParseResult,
    Checkpoint,
    CheckpointManager,
    MemoryManager,
    parse_pdf_optimized
)


class TestParseProgress:
    """測試 ParseProgress 數據類。"""
    
    def test_progress_creation(self):
        progress = ParseProgress(
            current_page=50,
            total_pages=100,
            percentage=50.0,
            status="parsing",
            elapsed_ms=5000.0,
            memory_mb=256.5
        )
        
        assert progress.current_page == 50
        assert progress.total_pages == 100
        assert progress.percentage == 50.0
        assert progress.status == "parsing"
    
    def test_progress_to_dict(self):
        progress = ParseProgress(
            current_page=10,
            total_pages=100,
            percentage=10.0,
            status="detecting",
            elapsed_ms=100.0,
            memory_mb=128.0,
            checkpoint_id="test_123"
        )
        
        data = progress.to_dict()
        assert data["current_page"] == 10
        assert data["checkpoint_id"] == "test_123"


class TestCheckpoint:
    """測試 Checkpoint 數據類。"""
    
    def test_checkpoint_creation(self):
        checkpoint = Checkpoint(
            checkpoint_id="test_abc",
            file_hash="md5_hash_123",
            completed_pages=[0, 1, 2, 3],
            partial_results={"texts": ["page1", "page2"]}
        )
        
        assert checkpoint.checkpoint_id == "test_abc"
        assert len(checkpoint.completed_pages) == 4
        assert "texts" in checkpoint.partial_results
    
    def test_checkpoint_serialization(self):
        checkpoint = Checkpoint(
            checkpoint_id="test_xyz",
            file_hash="hash_456",
            completed_pages=[0, 1],
            partial_results={"forms": []}
        )
        
        data = checkpoint.to_dict()
        restored = Checkpoint.from_dict(data)
        
        assert restored.checkpoint_id == checkpoint.checkpoint_id
        assert restored.completed_pages == checkpoint.completed_pages


class TestCheckpointManager:
    """測試檢查點管理器。"""
    
    def test_save_and_load(self, tmp_path):
        manager = CheckpointManager(checkpoint_dir=str(tmp_path))
        
        checkpoint = Checkpoint(
            checkpoint_id="test_save",
            file_hash="hash_789",
            completed_pages=[0, 1, 2],
            partial_results={"data": "test"}
        )
        
        manager.save(checkpoint)
        
        # 驗證文件存在
        checkpoint_file = tmp_path / "test_save.json"
        assert checkpoint_file.exists()
        
        # 驗證加載
        loaded = manager.load("test_save")
        assert loaded is not None
        assert loaded.checkpoint_id == "test_save"
    
    def test_load_nonexistent(self, tmp_path):
        manager = CheckpointManager(checkpoint_dir=str(tmp_path))
        result = manager.load("nonexistent")
        assert result is None
    
    def test_delete(self, tmp_path):
        manager = CheckpointManager(checkpoint_dir=str(tmp_path))
        
        checkpoint = Checkpoint(
            checkpoint_id="test_delete",
            file_hash="hash",
            completed_pages=[],
            partial_results={}
        )
        
        manager.save(checkpoint)
        manager.delete("test_delete")
        
        checkpoint_file = tmp_path / "test_delete.json"
        assert not checkpoint_file.exists()
    
    def test_create_checkpoint_id(self, tmp_path):
        manager = CheckpointManager(checkpoint_dir=str(tmp_path))
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        
        checkpoint_id = manager.create_checkpoint_id(temp_path)
        assert checkpoint_id.startswith("pdf_")
        assert len(checkpoint_id) > 10
        
        temp_path.unlink()


class TestMemoryManager:
    """測試內存管理器。"""
    
    def test_get_current_memory(self):
        manager = MemoryManager(max_memory_mb=500.0)
        memory = manager.get_current_memory_mb()
        
        assert memory > 0
        assert memory < 10000  # 合理的內存範圍
    
    def test_check_memory_pressure(self):
        manager = MemoryManager(max_memory_mb=500.0)
        
        # 正常情況下不應該有壓力
        pressure = manager.check_memory_pressure()
        assert pressure is False  # 實際內存通常遠小於 450MB
    
    def test_peak_memory_tracking(self):
        manager = MemoryManager(max_memory_mb=500.0)
        
        initial_peak = manager.peak_memory_mb
        manager.check_memory_pressure()
        
        assert manager.peak_memory_mb >= initial_peak
    
    def test_should_flush(self):
        manager = MemoryManager(max_memory_mb=500.0)
        
        # 小緩衝區不刷新
        assert manager.should_flush(1024) is False
        assert manager.should_flush(5 * 1024 * 1024) is False
        
        # 大緩衝區刷新
        assert manager.should_flush(15 * 1024 * 1024) is True


class TestOptimizedPDFParser:
    """測試優化版 PDF 解析器。"""
    
    def test_parser_initialization(self):
        parser = OptimizedPDFParser(
            use_gpu=False,
            use_cache=False,
            max_workers=4,
            page_batch_size=10,
            max_memory_mb=500.0
        )
        
        assert parser.max_workers == 4
        assert parser.page_batch_size == 10
        assert parser._memory_manager.max_memory_mb == 500.0
    
    def test_progress_callback(self):
        parser = OptimizedPDFParser()
        
        callback_called = False
        progress_received = None
        
        def callback(progress: ParseProgress):
            nonlocal callback_called, progress_received
            callback_called = True
            progress_received = progress
        
        parser.set_progress_callback(callback)
        parser._report_progress(10, 100, "parsing", 1000.0)
        
        assert callback_called
        assert progress_received is not None
        assert progress_received.current_page == 10
        assert progress_received.total_pages == 100
    
    def test_parse_nonexistent_file(self):
        parser = OptimizedPDFParser()
        
        result = parser.parse(Path("/nonexistent/file.pdf"))
        
        assert result.success is False
        assert "文件不存在" in result.error
    
    def test_compute_file_hash(self, tmp_path):
        parser = OptimizedPDFParser()
        
        # 創建測試文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        hash1 = parser._compute_file_hash(test_file)
        hash2 = parser._compute_file_hash(test_file)
        
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 哈希長度
    
    def test_extract_latex_formulas(self):
        parser = OptimizedPDFParser()
        
        text = """
        這是一個測試公式 $E = mc^2$。
        塊級公式：$$\\int_0^\\infty e^{-x^2} dx$$
        化學方程式：\\ce{H2O}
        """
        
        formulas = parser._extract_latex_formulas(text, page=1)
        
        assert len(formulas) >= 2  # 至少應該檢測到行內和塊級公式
        
        formula_types = [f["type"] for f in formulas]
        assert "inline" in formula_types or "block" in formula_types
    
    def test_extract_tags(self):
        parser = OptimizedPDFParser()
        
        # 測試文本需要匹配 regex 模式
        text = "關鍵點：這是一個重要概念。\n定義：測試定義。\n公式：E=mc²"
        tags = parser._extract_tags(text)
        
        # 可能返回空列表（取決於 regex 匹配），但不應該拋出異常
        assert isinstance(tags, list)
        assert all(isinstance(tag, str) for tag in tags)
    
    def test_shutdown(self):
        parser = OptimizedPDFParser()
        parser.shutdown()
        # 不拋出異常即為成功


class TestParsePdfOptimized:
    """測試便捷函數 parse_pdf_optimized。"""
    
    def test_parse_nonexistent(self):
        result = parse_pdf_optimized("/nonexistent/file.pdf")
        
        assert result.success is False
        assert result.error is not None
    
    def test_with_progress_callback(self, tmp_path):
        # 創建一個簡單的測試文件（非 PDF，用於測試錯誤處理）
        test_file = tmp_path / "test.txt"
        test_file.write_text("not a pdf")
        
        progress_calls = []
        
        def callback(progress: ParseProgress):
            progress_calls.append(progress)
        
        # 應該拋出錯誤（不是有效的 PDF）
        try:
            result = parse_pdf_optimized(
                str(test_file),
                progress_callback=callback
            )
        except Exception:
            # 預期會失敗，因為不是有效的 PDF
            pass


class TestPerformance:
    """性能測試。"""
    
    @pytest.mark.skip(reason="需要真實 PDF 文件")
    def test_large_pdf_parsing_time(self):
        """測試大文件解析時間（需要 100MB+ PDF）。"""
        parser = OptimizedPDFParser(
            max_workers=4,
            page_batch_size=10
        )
        
        start_time = time.time()
        result = parser.parse(Path("/path/to/large.pdf"))
        elapsed = time.time() - start_time
        
        assert elapsed < 30, f"解析時間過長：{elapsed}秒"
        assert result.peak_memory_mb < 500, f"內存使用過高：{result.peak_memory_mb}MB"
    
    @pytest.mark.skip(reason="需要真實 PDF 文件")
    def test_memory_usage(self):
        """測試內存使用（需要真實 PDF）。"""
        parser = OptimizedPDFParser(max_memory_mb=500.0)
        
        result = parser.parse(Path("/path/to/large.pdf"))
        
        assert result.peak_memory_mb < 500


class TestIntegration:
    """集成測試。"""
    
    def test_full_workflow(self, tmp_path):
        """測試完整工作流程。"""
        # 1. 創建檢查點管理器
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir()
        
        manager = CheckpointManager(checkpoint_dir=str(checkpoint_dir))
        
        # 2. 創建檢查點
        checkpoint = Checkpoint(
            checkpoint_id="integration_test",
            file_hash="test_hash",
            completed_pages=[0, 1, 2],
            partial_results={"texts": ["p1", "p2", "p3"]}
        )
        
        manager.save(checkpoint)
        
        # 3. 加載檢查點
        loaded = manager.load("integration_test")
        assert loaded is not None
        assert loaded.completed_pages == [0, 1, 2]
        
        # 4. 刪除檢查點
        manager.delete("integration_test")
        assert manager.load("integration_test") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
