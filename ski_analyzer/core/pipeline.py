"""
Единый pipeline для обработки видео от начала до конца
"""
from pathlib import Path
from typing import Optional, Dict

from .pose_extractor import PoseExtractor
from .angle_calculator import AngleCalculator
from .data_processor import DataProcessor
from .template_builder import TemplateBuilder
from .analyzer import SkiAnalyzer
from ..config.settings import (
    YOLO_MODEL_PATH, RESULTS_DIR, VIDEOS_DIR, TEMPLATE_FILE
)


class SkiAnalysisPipeline:
    """Единый pipeline для полной обработки видео"""
    
    def __init__(self, model_path: Optional[str] = None, results_dir: Optional[str] = None):
        """
        Инициализация pipeline
        
        Args:
            model_path: Путь к модели YOLO (по умолчанию из настроек)
            results_dir: Директория для результатов (по умолчанию из настроек)
        """
        if model_path is None:
            model_path = str(YOLO_MODEL_PATH)
        if results_dir is None:
            results_dir = RESULTS_DIR
        
        self.model_path = model_path
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Инициализируем компоненты
        self.pose_extractor = PoseExtractor(model_path)
        self.angle_calculator = AngleCalculator()
        self.data_processor = DataProcessor()
    
    def process_video(self, video_path: str, 
                     save_intermediate: bool = True,
                     save_annotated_video: bool = False) -> Dict[str, str]:
        """
        Полная обработка видео: извлечение позы → углы → обработка
        
        Args:
            video_path: Путь к входному видео
            save_intermediate: Сохранять ли промежуточные файлы
            save_annotated_video: Сохранять ли видео с аннотациями
            
        Returns:
            Словарь с путями к созданным файлам
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Видео не найдено: {video_path}")
        
        base_name = video_path.stem
        
        print(f"\n{'='*60}")
        print(f"Обработка видео: {video_path.name}")
        print(f"{'='*60}\n")
        
        # Шаг 1: Извлечение позы
        print("Шаг 1/3: Извлечение позы...")
        landmarks_csv = self.results_dir / f"{base_name}_landmarks.csv"
        video_output = self.results_dir / f"{base_name}_pose_output.mp4" if save_annotated_video else None
        
        _, landmarks_path = self.pose_extractor.extract_pose(
            str(video_path),
            output_csv=str(landmarks_csv) if save_intermediate else None,
            output_video=str(video_output) if save_annotated_video else None
        )
        
        # Шаг 2: Вычисление углов
        print("\nШаг 2/3: Вычисление углов...")
        angles_csv = self.results_dir / f"{base_name}_angles.csv"
        angles_df = self.angle_calculator.process_file(
            landmarks_path,
            output_path=str(angles_csv) if save_intermediate else None
        )
        
        # Шаг 3: Обработка данных (сглаживание и ресемплинг)
        print("\nШаг 3/3: Обработка данных (сглаживание и ресемплинг)...")
        resampled_csv = self.results_dir / f"{base_name}_angles_resampled.csv"
        processed_df = self.data_processor.process_angles(angles_df)
        
        # Всегда сохраняем resampled файл - он нужен для анализа
        processed_df.to_csv(resampled_csv, sep=';', index=False, encoding='utf-8-sig')
        if save_intermediate:
            print(f"✓ Обработанные данные сохранены в: {resampled_csv}")
        
        print(f"\n{'='*60}")
        print("✓ Обработка завершена!")
        print(f"{'='*60}\n")
        
        return {
            "landmarks": str(landmarks_csv) if save_intermediate else landmarks_path,
            "angles": str(angles_csv) if save_intermediate else None,
            "resampled": str(resampled_csv),  # Всегда сохраняем для анализа
            "video_annotated": str(video_output) if save_annotated_video else None
        }
    
    def analyze_user_video(self, video_path: str, 
                          template_path: Optional[str] = None,
                          save_intermediate: bool = True,
                          use_llm: bool = False,
                          llm_generator: Optional = None,
                          user_profile: Optional[Dict] = None) -> Dict:
        """
        Полная обработка и анализ пользовательского видео
        
        Args:
            video_path: Путь к видео пользователя
            template_path: Путь к эталону (по умолчанию из настроек)
            save_intermediate: Сохранять ли промежуточные файлы
            use_llm: Использовать ли LLM для генерации рекомендаций
            llm_generator: Экземпляр LLMRecommendationGenerator (если None и use_llm=True, создастся автоматически)
            user_profile: Профиль пользователя для LLM (уровень, опыт, цели)
            
        Returns:
            Словарь с результатами анализа и рекомендациями
        """
        # Обрабатываем видео
        files = self.process_video(video_path, save_intermediate=save_intermediate)
        
        # Анализируем
        if template_path is None:
            template_path = str(TEMPLATE_FILE)
        
        analyzer = SkiAnalyzer(template_path)
        report = analyzer.get_detailed_report(files["resampled"])
        
        # Генерируем LLM рекомендации если нужно
        llm_recommendations = None
        if use_llm:
            try:
                if llm_generator is None:
                    # Создаем генератор автоматически
                    from ..utils.llm_recommendations import LLMRecommendationGenerator
                    import os
                    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
                    if api_key:
                        provider = "gemini" if os.getenv("GEMINI_API_KEY") else "openai"
                        llm_generator = LLMRecommendationGenerator(
                            api_key=api_key,
                            provider=provider
                        )
                    else:
                        print("[WARNING] LLM API ключ не найден, пропускаем LLM рекомендации")
                        use_llm = False
                
                if llm_generator:
                    print("\nГенерация рекомендаций через LLM...")
                    llm_recommendations = llm_generator.generate_recommendations(
                        report,
                        user_profile=user_profile
                    )
                    print("✓ LLM рекомендации сгенерированы")
            except Exception as e:
                print(f"[WARNING] Ошибка при генерации LLM рекомендаций: {e}")
                print("Используются базовые рекомендации.")
        
        result = {
            "files": files,
            "analysis": report
        }
        
        # Добавляем LLM рекомендации если есть
        if llm_recommendations:
            result["llm_recommendations"] = llm_recommendations
        
        return result
    
    @staticmethod
    def build_template_from_directory(directory: Optional[str] = None, 
                                      pattern: str = "*_resampled.csv",
                                      output_path: Optional[str] = None) -> str:
        """
        Строит эталон из всех файлов в директории
        
        Args:
            directory: Директория для поиска (по умолчанию RESULTS_DIR)
            pattern: Паттерн для поиска файлов
            output_path: Путь для сохранения эталона
            
        Returns:
            Путь к созданному эталону
        """
        builder = TemplateBuilder()
        template_df = builder.build_from_directory(directory, pattern)
        
        if output_path is None:
            output_path = str(TEMPLATE_FILE)
        
        return output_path

