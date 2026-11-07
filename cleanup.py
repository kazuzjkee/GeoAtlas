#!/usr/bin/env python3
"""
Скрипт безопасной очистки корневой директории проекта GeoAtlas.
- Создает выделенную директорию public/maps (если не существует).
- Перемещает все сгенерированные файлы карт (*_quiz_map.html) из корня в public/maps/.
- Удаляет устаревшие дубликаты и временный мусор (index_2.html, index_4.html и др.).
"""

import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_DIR = os.path.join(BASE_DIR, 'public', 'maps')

# Список устаревших файлов и дубликатов для удаления
JUNK_FILES = [
    'index_2.html',
    'index_4.html',
    'index_old.html',
    'index_backup.html',
    'testovyy_region_quiz_map.html'
]

def run_cleanup():
    print("=" * 65)
    print("🧹 ЗАПУСК ОЧИСТКИ КОРНЕВОЙ ДИРЕКТОРИИ GEOATLAS")
    print("=" * 65)

    # 1. Проверка и создание целевой папки public/maps/
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR, exist_ok=True)
        print(f"📁 Создана директория: {os.path.relpath(MAPS_DIR, BASE_DIR)}")
    else:
        print(f"📁 Директория уже существует: {os.path.relpath(MAPS_DIR, BASE_DIR)}")

    # 2. Перемещение всех *_quiz_map.html из корня в public/maps/
    moved_maps = []
    skipped_maps = []

    for item in os.listdir(BASE_DIR):
        if item.endswith('_quiz_map.html'):
            src_file = os.path.join(BASE_DIR, item)
            dst_file = os.path.join(MAPS_DIR, item)

            if os.path.isfile(src_file):
                try:
                    # Если файл уже есть в public/maps, перезаписываем более свежим или копируем
                    shutil.copy2(src_file, dst_file)
                    os.remove(src_file)
                    moved_maps.append(item)
                except Exception as e:
                    print(f"  ❌ Ошибка перемещения {item}: {e}")
                    skipped_maps.append(item)

    print(f"\n🚚 Перемещено карт из корня в public/maps/: {len(moved_maps)}")
    if moved_maps:
        for m in moved_maps[:5]:
            print(f"   ✓ {m} -> public/maps/{m}")
        if len(moved_maps) > 5:
            print(f"   ... и еще {len(moved_maps) - 5} карт")

    # 3. Удаление устаревших файлов из корня
    deleted_junk = []
    for junk in JUNK_FILES:
        junk_path = os.path.join(BASE_DIR, junk)
        if os.path.exists(junk_path) and os.path.isfile(junk_path):
            try:
                os.remove(junk_path)
                deleted_junk.append(junk)
                print(f"🗑️  Удален устаревший файл: {junk}")
            except Exception as e:
                print(f"❌ Ошибка удаления {junk}: {e}")

    # 4. Проверка временных файлов *.tmp
    for item in os.listdir(BASE_DIR):
        if item.endswith('.tmp') or item.endswith('.temp'):
            tpath = os.path.join(BASE_DIR, item)
            if os.path.isfile(tpath):
                try:
                    os.remove(tpath)
                    deleted_junk.append(item)
                    print(f"🗑️  Удален временный файл: {item}")
                except Exception:
                    pass

    print("\n" + "=" * 65)
    print("🎉 ОЧИСТКА ЗАВЕРШЕНА!")
    print(f"   • Перемещено карт в public/maps/: {len(moved_maps)}")
    print(f"   • Удалено устаревших файлов: {len(deleted_junk)}")
    total_in_maps = len([f for f in os.listdir(MAPS_DIR) if f.endswith('.html')])
    print(f"   • Всего карт в public/maps/: {total_in_maps}")
    print("=" * 65)

if __name__ == '__main__':
    run_cleanup()
