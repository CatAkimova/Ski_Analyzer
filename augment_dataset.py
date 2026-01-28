"""
Скрипт для увеличения датасета через аугментацию видео
Использование:
    python augment_dataset.py --input Ski.Videos/Professional --output data/augmented/good --variations 5
"""
import argparse
from pathlib import Path
from ski_analyzer.ml.dataset_generator import VideoAugmenter


def main():
    parser = argparse.ArgumentParser(
        description="Увеличение датасета через аугментацию видео"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Директория с исходными видео"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Директория для сохранения аугментированных видео"
    )
    parser.add_argument(
        "--variations",
        type=int,
        default=5,
        help="Количество вариаций на каждое видео (по умолчанию: 5)"
    )
    
    args = parser.parse_args()
    
    # Проверяем входную директорию
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"✗ Директория не найдена: {input_path}")
        return
    
    # Создаем выходную директорию
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Входная директория: {input_path}")
    print(f"Выходная директория: {output_path}")
    print(f"Вариаций на видео: {args.variations}")
    print("-" * 60)
    
    # Создаем аугментатор
    augmenter = VideoAugmenter()
    
    # Обрабатываем видео
    created_files = augmenter.create_dataset_variations(
        str(input_path),
        str(output_path),
        variations_per_video=args.variations
    )
    
    print("-" * 60)
    print(f"✓ Создано {len(created_files)} аугментированных видео")
    print(f"✓ Сохранено в: {output_path}")


if __name__ == "__main__":
    main()



