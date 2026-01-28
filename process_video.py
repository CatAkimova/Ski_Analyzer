"""
Главный скрипт для обработки видео
Использование:
    python process_video.py <путь_к_видео> [--template <путь_к_эталону>] [--analyze] [--use-llm] [--save-all]
"""
import argparse
import sys
import os
from pathlib import Path

from ski_analyzer.core.pipeline import SkiAnalysisPipeline
from ski_analyzer.config.settings import TEMPLATE_FILE

# Загрузить ключ из .env если есть
env_file = Path(".env")
if env_file.exists():
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                os.environ["GEMINI_API_KEY"] = key
                break
            elif line.startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                os.environ["OPENAI_API_KEY"] = key
                break


def main():
    parser = argparse.ArgumentParser(
        description="Обработка видео для анализа техники катания на лыжах"
    )
    parser.add_argument("video", type=str, help="Путь к видео файлу")
    parser.add_argument(
        "--template", 
        type=str, 
        default=str(TEMPLATE_FILE),
        help=f"Путь к файлу эталона (по умолчанию: {TEMPLATE_FILE})"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Выполнить анализ и показать рекомендации"
    )
    parser.add_argument(
        "--save-all",
        action="store_true",
        help="Сохранить все промежуточные файлы и видео с аннотациями"
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Использовать LLM (Gemini) для генерации рекомендаций (требует --analyze)"
    )
    parser.add_argument(
        "--build-template",
        action="store_true",
        help="Построить эталон из всех resampled файлов в results/"
    )
    
    args = parser.parse_args()
    
    # Построение эталона
    if args.build_template:
        print("Построение эталона из файлов в results/...")
        try:
            template_path = SkiAnalysisPipeline.build_template_from_directory()
            print(f"✓ Эталон успешно создан: {template_path}")
        except Exception as e:
            print(f"✗ Ошибка при построении эталона: {e}")
            sys.exit(1)
        return
    
    # Проверяем наличие видео
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"✗ Видео не найдено: {video_path}")
        sys.exit(1)
    
    # Создаем pipeline
    try:
        pipeline = SkiAnalysisPipeline()
    except Exception as e:
        print(f"✗ Ошибка инициализации pipeline: {e}")
        sys.exit(1)
    
    # Обрабатываем видео
    try:
        if args.analyze:
            # Полный анализ
            result = pipeline.analyze_user_video(
                str(video_path),
                template_path=args.template if args.template != str(TEMPLATE_FILE) else None,
                save_intermediate=args.save_all,
                use_llm=args.use_llm  # Использовать LLM если указан флаг
            )
            
            # Выводим результаты
            print("\n" + "="*60)
            print("РЕЗУЛЬТАТЫ АНАЛИЗА")
            print("="*60)
            print(f"\nОбщий балл: {result['analysis']['overall_score']}/100")
            
            print("\nДетальный анализ по углам:")
            for fb in result['analysis']['angle_analysis']:
                angle_name = fb['angle']
                angle_ru = {
                    "left_knee_angle": "Левое колено",
                    "right_knee_angle": "Правое колено",
                    "left_body_angle": "Наклон корпуса (левая сторона)",
                    "right_body_angle": "Наклон корпуса (правая сторона)"
                }.get(angle_name, angle_name)
                
                print(f"\n  {angle_ru}:")
                print(f"    Доля фазы вне нормы: {fb['percent_bad']:.1f}%")
                print(f"    Среднее отклонение: {fb['mean_diff_deg']:+.1f}°")
                print(f"    Максимальное отклонение: {fb['max_diff_deg']:.1f}°")
                if fb['is_critical']:
                    print(f"    ⚠ Требует внимания!")
            
            print("\nБазовые рекомендации:")
            for i, rec in enumerate(result['analysis']['recommendations'], 1):
                print(f"  {i}. {rec}")
            
            # LLM рекомендации если есть
            if 'llm_recommendations' in result and result['llm_recommendations']:
                print("\n" + "-"*60)
                print("Рекомендации от Gemini:")
                print("-"*60)
                for i, rec in enumerate(result['llm_recommendations'], 1):
                    if not rec.startswith("Ошибка"):
                        print(f"  {i}. {rec}")
                    else:
                        print(f"  ⚠ {rec}")
            
            print("\n" + "="*60)
            
        else:
            # Только обработка
            files = pipeline.process_video(
                str(video_path),
                save_intermediate=args.save_all,
                save_annotated_video=args.save_all
            )
            print("\nСозданные файлы:")
            for key, path in files.items():
                if path:
                    print(f"  {key}: {path}")
    
    except Exception as e:
        print(f"✗ Ошибка при обработке: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

