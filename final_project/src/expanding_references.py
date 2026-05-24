from pathlib import Path


REFERENCE_START = '@::'
REFERENCE_END = '::'
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


def expand_references(message: str) -> str:
    expanded_parts = []
    current_index = 0

    while current_index < len(message):
        reference_start = message.find(REFERENCE_START, current_index)

        if reference_start == -1:
            expanded_parts.append(message[current_index:])
            break

        path_start = reference_start + len(REFERENCE_START)
        reference_end = message.find(REFERENCE_END, path_start)

        if reference_end == -1:
            expanded_parts.append(message[current_index:])
            break

        path_text = message[path_start:reference_end]

        expanded_parts.append(message[current_index:reference_start])
        expanded_parts.append(_read_referenced_file(path_text))

        current_index = reference_end + len(REFERENCE_END)

    return ''.join(expanded_parts)


def _read_referenced_file(file_path_text: str) -> str:
    file_path = Path(file_path_text).expanduser()

    if not file_path.exists():
        raise ValueError(f'Файл не найден: {file_path}')

    if not file_path.is_file():
        raise ValueError(f'Путь не является файлом: {file_path}')

    if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f'Файл слишком большой: {file_path}. Максимум 5 МБ.')

    try:
        return file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError as error:
        raise ValueError(f'Файл не является текстовым UTF-8 файлом: {file_path}') from error
    except OSError as error:
        raise ValueError(f'Не удалось прочитать файл: {file_path}') from error
