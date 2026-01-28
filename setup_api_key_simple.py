"""
Простой способ установки API ключа - через .env файл
"""
import os
from pathlib import Path

def setup_api_key():
    """Создает .env файл с API ключом"""
    
    print("=" * 60)
    print("Настройка API ключа через .env файл")
    print("=" * 60)
    
    # Проверяем, есть ли уже .env
    env_file = Path(".env")
    if env_file.exists():
        print("\n⚠ Файл .env уже существует.")
        response = input("Перезаписать? (y/n): ")
        if response.lower() != 'y':
            print("Отменено.")
            return
    
    # Запрашиваем ключ
    print("\nВведите ваш OpenAI API ключ:")
    print("(начинается с sk-, можно скопировать с https://platform.openai.com/api-keys)")
    api_key = input("API ключ: ").strip()
    
    if not api_key:
        print("❌ Ключ не введен!")
        return
    
    if not api_key.startswith("sk-"):
        print("⚠ Предупреждение: ключ должен начинаться с 'sk-'")
        response = input("Продолжить? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Создаем .env файл
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        
        print("\n✅ Файл .env создан успешно!")
        print("   API ключ сохранен в .env")
        print("\n📝 Теперь можно использовать:")
        print("   python test_llm_connection.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка при создании файла: {e}")

if __name__ == "__main__":
    setup_api_key()
