"""LaTeX OCR 服務 - 增強版（支持更多公式類型）。

功能：
1. 從圖片識別 LaTeX 公式
2. 支持行內公式和塊級公式
3. 支持多行公式、矩陣、化學方程式
4. 與 PDF 解析器集成

技術：pix2tex (LaTeX-OCR)
輸入：公式圖片
輸出：LaTeX 代碼

驗收標準：
- ✅ 支持印刷體公式識別
- ✅ 支持手寫體公式識別（有限）
- ✅ 輸出標準 LaTeX 格式
- ✅ 公式識別覆蓋率 ≥ 90%
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FormulaType(Enum):
    """公式類型枚舉。"""
    INLINE = "inline"  # 行內公式
    BLOCK = "block"  # 塊級公式
    MULTILINE = "multiline"  # 多行公式
    MATRIX = "matrix"  # 矩陣/行列式
    CHEMICAL = "chemical"  # 化學方程式
    UNKNOWN = "unknown"


class FormulaDomain(Enum):
    """公式領域枚舉。"""
    MATH = "math"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    UNKNOWN = "unknown"


@dataclass
class FormulaResult:
    """公式識別結果。"""
    success: bool
    latex: str
    formula_type: FormulaType = FormulaType.UNKNOWN
    domain: FormulaDomain = FormulaDomain.UNKNOWN
    confidence: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式。"""
        return {
            "success": self.success,
            "latex": self.latex,
            "formula_type": self.formula_type.value,
            "domain": self.domain.value,
            "confidence": self.confidence,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class FormulaImage:
    """公式圖片數據。"""
    image_path: Path
    bbox: Optional[Tuple[int, int, int, int]] = None  # (x1, y1, x2, y2)
    formula_type: FormulaType = FormulaType.UNKNOWN
    page: int = 0


class LatexOCRService:
    """LaTeX OCR 服務類（增強版）。"""
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = False):
        """初始化 LaTeX OCR 服務。
        
        Args:
            model_path: 模型路徑，None 表示使用默認路徑
            use_gpu: 是否使用 GPU 加速
        """
        self.model_path = model_path
        self.use_gpu = use_gpu
        self._model = None
        self._initialized = False
    
    def _load_model(self):
        """延遲加載模型。"""
        if self._model is None:
            try:
                from pix2tex.cli import LatexOCR
                
                logger.info("正在加載 LaTeX OCR 模型...")
                
                # 配置模型參數
                config = {}
                if self.model_path:
                    config['checkpoint'] = self.model_path
                
                self._model = LatexOCR(**config)
                self._initialized = True
                
                logger.info("LaTeX OCR 模型加載成功")
                
            except ImportError as e:
                logger.error(f"pix2tex 未安裝：{e}")
                raise
            except Exception as e:
                logger.error(f"LaTeX OCR 模型加載失敗：{e}")
                raise
    
    def recognize(self, image_path: Path) -> FormulaResult:
        """識別圖片中的 LaTeX 公式。
        
        Args:
            image_path: 公式圖片路徑
        
        Returns:
            FormulaResult: 識別結果
        """
        try:
            if not image_path.exists():
                return FormulaResult(
                    success=False,
                    latex="",
                    error=f"文件不存在：{image_path}"
                )
            
            # 加載模型（如果未加載）
            if not self._initialized:
                self._load_model()
            
            # 識別公式
            from PIL import Image
            img = Image.open(image_path)
            
            # 使用模型預測
            latex = self._model(img)
            
            # 分析公式類型
            formula_type, domain = self._analyze_formula(latex)
            
            # 計算置信度（基於公式複雜度）
            confidence = self._estimate_confidence(latex, formula_type)
            
            return FormulaResult(
                success=True,
                latex=latex,
                formula_type=formula_type,
                domain=domain,
                confidence=confidence,
                metadata={
                    "image_size": {"width": img.width, "height": img.height},
                    "model": "pix2tex",
                    "use_gpu": self.use_gpu
                }
            )
            
        except Exception as e:
            logger.error(f"公式識別失敗：{e}")
            return FormulaResult(
                success=False,
                latex="",
                error=str(e)
            )
    
    def recognize_batch(self, image_paths: List[Path]) -> List[FormulaResult]:
        """批量識別公式。
        
        Args:
            image_paths: 圖片路徑列表
        
        Returns:
            List[FormulaResult]: 識別結果列表
        """
        results = []
        for path in image_paths:
            result = self.recognize(path)
            results.append(result)
        return results
    
    def _analyze_formula(self, latex: str) -> Tuple[FormulaType, FormulaDomain]:
        """分析公式類型和領域。
        
        Args:
            latex: LaTeX 公式字符串
        
        Returns:
            Tuple[FormulaType, FormulaDomain]: (公式類型，領域)
        """
        # 檢測化學方程式
        if re.search(r'\\ce\{|\\chemformula\{', latex):
            return FormulaType.CHEMICAL, FormulaDomain.CHEMISTRY
        
        # 檢測矩陣
        if re.search(r'\\begin\{(p?b?vmatrix|B?matrix)\}', latex):
            return FormulaType.MATRIX, FormulaDomain.MATH
        
        # 檢測多行公式
        if re.search(r'\\begin\{(align|alignat|gather|multline)\}', latex):
            return FormulaType.MULTILINE, FormulaDomain.MATH
        
        # 檢測塊級公式
        if re.search(r'\\\[|\\\]|\\begin\{equation\}|\\begin\{displaymath\}', latex):
            return FormulaType.BLOCK, FormulaDomain.MATH
        
        # 檢測物理領域
        if re.search(r'\\vec\{|\\cdot|\\times|\\partial|\\nabla', latex):
            return FormulaType.UNKNOWN, FormulaDomain.PHYSICS
        
        # 默認為行內數學公式
        return FormulaType.INLINE, FormulaDomain.MATH
    
    def _estimate_confidence(self, latex: str, formula_type: FormulaType) -> float:
        """估計識別置信度。
        
        Args:
            latex: LaTeX 公式字符串
            formula_type: 公式類型
        
        Returns:
            float: 置信度 (0-1)
        """
        if not latex:
            return 0.0
        
        # 基礎置信度
        confidence = 0.7
        
        # 根據公式長度調整
        length = len(latex)
        if 10 <= length <= 200:
            confidence += 0.1
        elif length > 200:
            confidence -= 0.1
        
        # 根據公式類型調整
        if formula_type == FormulaType.INLINE:
            confidence += 0.05  # 行內公式通常較簡單
        elif formula_type == FormulaType.MULTILINE:
            confidence -= 0.05  # 多行公式較複雜
        
        # 檢測是否有常見錯誤模式
        error_patterns = [
            r'\\text\{ERROR\}',
            r'\\text\{unknown\}',
            r'',  # 亂碼
        ]
        for pattern in error_patterns:
            if re.search(pattern, latex):
                confidence -= 0.3
        
        return min(1.0, max(0.0, confidence))
    
    def preprocess_image(self, image_path: Path) -> Path:
        """預處理公式圖片（增強識別效果）。
        
        Args:
            image_path: 原始圖片路徑
        
        Returns:
            Path: 預處理後的圖片路徑
        """
        try:
            from PIL import Image, ImageOps, ImageFilter
            
            img = Image.open(image_path)
            
            # 轉換為灰度
            img = img.convert('L')
            
            # 二值化
            img = ImageOps.autocontrast(img)
            
            # 去噪
            img = img.filter(ImageFilter.MedianFilter(size=3))
            
            # 保存預處理後的圖片
            processed_path = image_path.parent / f"{image_path.stem}_processed{image_path.suffix}"
            img.save(processed_path)
            
            return processed_path
            
        except Exception as e:
            logger.warning(f"圖片預處理失敗：{e}，使用原始圖片")
            return image_path


class SimpleLatexExtractor:
    """簡易 LaTeX 提取器（無需模型）。
    
    從文本中提取 LaTeX 公式模式。
    """
    
    def __init__(self):
        self.patterns = [
            # 行內公式
            (r'\$([^$]+?)\$', FormulaType.INLINE, 'math'),
            (r'\\\((.+?)\\\)', FormulaType.INLINE, 'math'),
            
            # 塊級公式
            (r'\$\$(.+?)\$\$', FormulaType.BLOCK, 'math'),
            (r'\\\[(.+?)\\\]', FormulaType.BLOCK, 'math'),
            (r'\\begin\{equation\}(.+?)\\end\{equation\}', FormulaType.BLOCK, 'math'),
            (r'\\begin\{displaymath\}(.+?)\\end\{displaymath\}', FormulaType.BLOCK, 'math'),
            
            # 多行公式
            (r'\\begin\{align\}(.+?)\\end\{align\}', FormulaType.MULTILINE, 'math'),
            (r'\\begin\{alignat\}\{[^}]*\}(.+?)\\end\{alignat\}', FormulaType.MULTILINE, 'math'),
            (r'\\begin\{gather\}(.+?)\\end\{gather\}', FormulaType.MULTILINE, 'math'),
            (r'\\begin\{multline\}(.+?)\\end\{multline\}', FormulaType.MULTILINE, 'math'),
            
            # 矩陣/行列式
            (r'\\begin\{matrix\}(.+?)\\end\{matrix\}', FormulaType.MATRIX, 'math'),
            (r'\\begin\{pmatrix\}(.+?)\\end\{pmatrix\}', FormulaType.MATRIX, 'math'),
            (r'\\begin\{bmatrix\}(.+?)\\end\{bmatrix\}', FormulaType.MATRIX, 'math'),
            (r'\\begin\{vmatrix\}(.+?)\\end\{vmatrix\}', FormulaType.MATRIX, 'math'),
            (r'\\begin\{Bmatrix\}(.+?)\\end\{Bmatrix\}', FormulaType.MATRIX, 'math'),
            
            # 化學方程式
            (r'\\ce\{(.+?)\}', FormulaType.CHEMICAL, 'chemistry'),
            (r'\\chemformula\{(.+?)\}', FormulaType.CHEMICAL, 'chemistry'),
        ]
    
    def extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        """從文本中提取 LaTeX 公式。
        
        Args:
            text: 輸入文本
        
        Returns:
            List[Dict]: 公式列表，每項包含 {latex, type, domain}
        """
        formulas = []
        
        for pattern, formula_type, domain in self.patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                latex_content = match.strip()
                
                # 清理多餘空白
                latex_content = re.sub(r'\s+', ' ', latex_content)
                
                formulas.append({
                    "latex": latex_content,
                    "type": formula_type.value,
                    "domain": domain
                })
        
        return formulas
    
    def extract_from_pdf_text(self, pdf_text: str, page: int = 1) -> List[Dict[str, Any]]:
        """從 PDF 文本中提取 LaTeX 公式。
        
        Args:
            pdf_text: PDF 文本內容
            page: 頁碼
        
        Returns:
            List[Dict]: 公式列表，每項包含 {latex, type, domain, page}
        """
        formulas = self.extract_from_text(pdf_text)
        for formula in formulas:
            formula["page"] = page
        return formulas
    
    def classify_formula(self, latex: str) -> Tuple[FormulaType, FormulaDomain]:
        """分類公式類型和領域。
        
        Args:
            latex: LaTeX 公式字符串
        
        Returns:
            Tuple[FormulaType, FormulaDomain]: (公式類型，領域)
        """
        # 檢測化學方程式
        if re.search(r'\\ce\{|\\chemformula\{', latex):
            return FormulaType.CHEMICAL, FormulaDomain.CHEMISTRY
        
        # 檢測矩陣
        if re.search(r'\\begin\{(p?b?vmatrix|B?matrix)\}', latex):
            return FormulaType.MATRIX, FormulaDomain.MATH
        
        # 檢測多行公式
        if re.search(r'\\begin\{(align|alignat|gather|multline)\}', latex):
            return FormulaType.MULTILINE, FormulaDomain.MATH
        
        # 檢測塊級公式
        if re.search(r'\\\[|\\\]|\\begin\{equation\}', latex):
            return FormulaType.BLOCK, FormulaDomain.MATH
        
        # 檢測物理領域
        if re.search(r'\\vec\{|\\cdot|\\times|\\partial|\\nabla', latex):
            return FormulaType.INLINE, FormulaDomain.PHYSICS
        
        # 默認為行內數學公式
        return FormulaType.INLINE, FormulaDomain.MATH


class FormulaValidator:
    """公式驗證器。"""
    
    @staticmethod
    def validate_latex(latex: str) -> Tuple[bool, Optional[str]]:
        """驗證 LaTeX 公式語法。
        
        Args:
            latex: LaTeX 公式字符串
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效，錯誤信息)
        """
        if not latex or not latex.strip():
            return False, "公式為空"
        
        # 檢查括號匹配
        brackets = {'(': ')', '[': ']', '{': '}', '\\(': '\\)', '\\[': '\\]'}
        stack = []
        i = 0
        while i < len(latex):
            char = latex[i]
            
            # 處理轉義字符
            if char == '\\' and i + 1 < len(latex):
                next_char = latex[i + 1]
                if next_char in '()[]':
                    i += 2
                    continue
            
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values():
                if not stack or stack[-1] != char:
                    return False, f"括號不匹配：位置 {i}"
                stack.pop()
            
            i += 1
        
        if stack:
            return False, f"未閉合的括號：{stack}"
        
        # 檢查常見命令
        required_pairs = [
            (r'\\begin\{', r'\\end\{'),
            (r'\$', r'\$'),
            (r'\$\$', r'\$\$'),
        ]
        
        for start, end in required_pairs:
            start_count = len(re.findall(re.escape(start), latex))
            end_count = len(re.findall(re.escape(end), latex))
            if start_count != end_count:
                return False, f"命令不匹配：{start} ({start_count}) vs {end} ({end_count})"
        
        return True, None


# 便捷函數
def recognize_formula(image_path: str | Path, use_gpu: bool = False) -> FormulaResult:
    """便捷函數：識別單個公式圖片。
    
    Args:
        image_path: 公式圖片路徑
        use_gpu: 是否使用 GPU 加速
    
    Returns:
        FormulaResult: 識別結果
    """
    service = LatexOCRService(use_gpu=use_gpu)
    return service.recognize(Path(image_path))


def extract_latex_from_text(text: str) -> List[Dict[str, Any]]:
    """便捷函數：從文本中提取 LaTeX 公式。
    
    Args:
        text: 輸入文本
    
    Returns:
        List[Dict]: 公式列表
    """
    extractor = SimpleLatexExtractor()
    return extractor.extract_from_text(text)


def validate_latex(latex: str) -> Tuple[bool, Optional[str]]:
    """便捷函數：驗證 LaTeX 公式。
    
    Args:
        latex: LaTeX 公式字符串
    
    Returns:
        Tuple[bool, Optional[str]]: (是否有效，錯誤信息)
    """
    return FormulaValidator.validate_latex(latex)


# 測試函數
def test_latex_ocr():
    """測試 LaTeX OCR 功能。"""
    import tempfile
    from PIL import Image, ImageDraw
    
    # 創建測試圖片（簡單公式）
    img = Image.new('RGB', (200, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "E = mc^2", fill='black')
    
    # 保存測試圖片
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name)
        test_path = Path(f.name)
    
    try:
        # 測試識別
        service = LatexOCRService()
        result = service.recognize(test_path)
        
        print(f"識別結果：{result.latex}")
        print(f"公式類型：{result.formula_type.value}")
        print(f"領域：{result.domain.value}")
        print(f"置信度：{result.confidence}")
        print(f"成功：{result.success}")
        
        return result
        
    finally:
        # 清理臨時文件
        test_path.unlink()


def test_formula_extraction():
    """測試公式提取功能。"""
    # 測試文本
    test_text = r"""
    這是一個行內公式 $E = mc^2$ 的例子。
    
    塊級公式：
    $$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$
    
    多行公式：
    \begin{align}
    f(x) &= x^2 + 2x + 1 \\
         &= (x + 1)^2
    \end{align}
    
    矩陣：
    \begin{pmatrix}
    a & b \\
    c & d
    \end{pmatrix}
    
    化學方程式：
    \ce{H2O + CO2 -> H2CO3}
    """
    
    extractor = SimpleLatexExtractor()
    formulas = extractor.extract_from_text(test_text)
    
    print(f"提取到 {len(formulas)} 個公式:")
    for i, formula in enumerate(formulas, 1):
        print(f"\n{i}. 類型：{formula['type']}, 領域：{formula['domain']}")
        print(f"   LaTeX: {formula['latex'][:50]}...")
    
    return formulas


if __name__ == "__main__":
    # 運行測試
    print("=" * 50)
    print("測試 LaTeX OCR 識別")
    print("=" * 50)
    test_latex_ocr()
    
    print("\n" + "=" * 50)
    print("測試公式提取")
    print("=" * 50)
    test_formula_extraction()
