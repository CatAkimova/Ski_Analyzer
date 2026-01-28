"""
Основные модули обработки
"""
from .pose_extractor import PoseExtractor
from .angle_calculator import AngleCalculator
from .data_processor import DataProcessor
from .template_builder import TemplateBuilder
from .analyzer import SkiAnalyzer

__all__ = [
    'PoseExtractor',
    'AngleCalculator',
    'DataProcessor',
    'TemplateBuilder',
    'SkiAnalyzer'
]

