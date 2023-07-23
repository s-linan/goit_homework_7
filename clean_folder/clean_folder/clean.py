from pathlib import Path
import shutil
import re
import sys

IMAGES = []
VIDEOS = []
DOCUMENTS = []
AUDIO = []
ARCHIVES = []
OTHER = []

REGISTER_EXTENSION = {
    'JPEG': IMAGES, 'PNG': IMAGES, 'JPG': IMAGES, 'SVG': IMAGES, 'BMP': IMAGES,
    'AVI': VIDEOS, 'MP4': VIDEOS, 'MOV': VIDEOS, 'MKV': VIDEOS,
    'DOC': DOCUMENTS, 'DOCX': DOCUMENTS, 'TXT': DOCUMENTS, 'PDF': DOCUMENTS, 'XLSX': DOCUMENTS, 'PPTX': DOCUMENTS,
    'MP3': AUDIO, 'OGG': AUDIO, 'WAV': AUDIO, 'AMR': AUDIO,
    'ZIP': ARCHIVES, 'GZ': ARCHIVES, 'TAR': ARCHIVES
}

FOLDERS = []
EXTENSION = set()
UNKNOWN = set()

def get_extension(filename: str) -> str:
    return Path(filename).suffix[1:].upper() # перетворюємо розширення файлу на назву папки .jpg -> JPG (суфікс[1:] пропускає 1 символ, тобто крапку)



def scan(folder: Path) -> None:
    for item in folder.iterdir():
        if item.is_dir():
            # Якщо це папка то додаємо її до списку FOLDERS і переходимо до наступної папки
            # Перевіряємо, щоб папка не була тією, в яку ми складаємо файли
            if item.name not in ('images', 'videos', 'audio', 'documents', 'images', 'other'):
                FOLDERS.append(item)
                # скануємо вкладену папку
                scan(item) # рекурсія
            continue # переходимо до наступного елемента
        # Робота з файлом
        ext = get_extension(item.name) # беремо розширення файлу
        fullname = folder / item.name # беремо шлях до файлу
        if not ext: # якщо файл не має розширення то додаємо до невідомих
            OTHER.append(fullname)
        else:
            try:
                container = REGISTER_EXTENSION[ext]
                EXTENSION.add(ext)
                container.append(fullname)
            except KeyError:
                # якщо не зареєстрували розширення у REGISTER_EXTENSION, то додаємо до невідомих
                UNKNOWN.add(ext)
                OTHER.append(fullname)

if __name__ == "__main__":
    folder_to_scan = sys.argv[1]
    print(f'Start in folder {folder_to_scan}')
    scan(Path(folder_to_scan))
    print(f'Images: {IMAGES}')
    print(f'Videos: {VIDEOS}')
    print(f'Documents: {DOCUMENTS}')
    print(f'Audio: {AUDIO}')
    print(f'Archives: {ARCHIVES}')
    print(f'Other: {OTHER}')
    print(f'Types of files in folder: {EXTENSION}')
    print(f'Unknown files of types: {UNKNOWN}')
    print(FOLDERS[::-1]) # виводить усі знайдені папки у нашій папці


CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", "ji", "g")
TRANS = {}

for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    TRANS[ord(c)] = l
    TRANS[ord(c.upper())] = l.upper()

def normalize(name: str) -> str:
    t_name = name.translate(TRANS)
    if '.' in t_name:
        split_t_name = t_name.split('.')
        suffix = '.' + split_t_name.pop()
        t_name = '.'.join(split_t_name)
        t_name = re.sub(r'\W', '_', t_name) + suffix
        print(t_name)
    else:
        t_name = re.sub(r'\W', '_', t_name)
    return t_name


def handle_media(filename: Path, target_folder: Path) -> None:
    target_folder.mkdir(exist_ok=True, parents=True)
    filename.replace(target_folder / normalize(filename.name))

def handle_other(filename: Path, target_folder: Path) -> None:
    target_folder.mkdir(exist_ok=True, parents=True)
    filename.replace(target_folder / normalize(filename.name))

def handle_archive(filename: Path, target_folder: Path) -> None:
    target_folder.mkdir(exist_ok=True, parents=True) # папка для архіву
    folder_for_file = target_folder / normalize(filename.name.replace(filename.suffix, ''))
    folder_for_file.mkdir(exist_ok=True, parents=True)
    try:
        shutil.unpack_archive(filename, folder_for_file)
    except shutil.ReadError:
        print("It's not archive")
        folder_for_file.rmdir()
    filename.unlink()

def handle_folder(folder: Path):
    try:
        folder.rmdir()
    except OSError:
        print(f"Can't delete folder: {folder}")

def main(folder: Path):
    scan(folder)
    for file in IMAGES:
        handle_media(file, folder / 'Images')
    for file in VIDEOS:
        handle_media(file, folder / 'Videos')
    for file in DOCUMENTS:
        handle_media(file, folder / 'Documents')
    for file in AUDIO:
        handle_media(file, folder / 'Audio')
    for file in ARCHIVES:
        handle_archive(file, folder / 'Archives')
    for file in OTHER:
        handle_other(file, folder / 'Other')
    for folder in FOLDERS[::-1]:
        handle_folder(folder)

def start():
    try:
        if len(sys.argv) > 2:
            print('Enter only one destination/folder name!')
        elif len(sys.argv) < 2:
            print('Enter destination/folder name!')
        else:
            folder_for_scan = Path(sys.argv[1])
            print(f'Start in folder {folder_for_scan.resolve()}')
            main(folder_for_scan.resolve())
    except IndexError:
        print('Missing folder name!')
    except FileNotFoundError:
        print('Folder not found!')
