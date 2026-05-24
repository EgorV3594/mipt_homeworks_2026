from dataclasses import dataclass
from pathlib import Path

from src.expanding_references import MAX_FILE_SIZE_BYTES
from src.config import AppConfig
from src.llm import ask_llm_in_filechunk_mode


QUIT_COMMAND = '\\q'


@dataclass(frozen=True)
class ChunkOptions:
    paragraph_count: int = 1
    chunk_length: int | None = None
    auto_run: bool = False


def run_file_chunk_mode(args: list[str], config: AppConfig) -> bool:
    try:
        options = _parse_chunk_options(args)

        file_text = _ask_file_text()
        if file_text is None:
            return True

        user_prompt = _ask_user_prompt()
        if user_prompt is None:
            return True

        chunks = _split_text_into_chunks(file_text, options)
        if not chunks:
            print('Файл пустой, обрабатывать нечего.')
            return True

        print('Принято. Начинаю обработку:')
        _process_chunks(chunks, user_prompt, options.auto_run, config)
    except ValueError as error:
        print(f'Ошибка режима /file_chunk: {error}')
    except KeyboardInterrupt:
        print('\nОбработка файла прервана.')
    except RuntimeError as error:
        print(f'Ошибка обращения к LLM: {error}')

    return True


def _parse_chunk_options(args: list[str]) -> ChunkOptions:
    paragraph_count = 1
    chunk_length = None
    auto_run = False
    paragraph_was_set = False

    for arg in args:
        if arg == '-y':
            auto_run = True
            continue

        if arg.startswith('paragraph='):
            paragraph_count = _parse_positive_int_arg(arg, 'paragraph')
            paragraph_was_set = True
            continue

        if arg.startswith('len='):
            chunk_length = _parse_positive_int_arg(arg, 'len')
            continue

        raise ValueError(f'неизвестный параметр: {arg}')

    if paragraph_was_set and chunk_length is not None:
        raise ValueError('нельзя одновременно использовать paragraph и len.')

    return ChunkOptions(
        paragraph_count=paragraph_count,
        chunk_length=chunk_length,
        auto_run=auto_run,
    )


def _parse_positive_int_arg(arg: str, name: str) -> int:
    _, value = arg.split('=', maxsplit=1)
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise ValueError(f'параметр {name} должен быть целым числом.') from error

    if parsed_value <= 0:
        raise ValueError(f'параметр {name} должен быть положительным.')

    return parsed_value


def _ask_file_text() -> str | None:
    print('Введите путь до файла')
    file_path_text = input('> ').strip()
    if file_path_text == QUIT_COMMAND:
        return None

    return _read_file(file_path_text)


def _read_file(file_path_text: str) -> str:
    path = Path(file_path_text).expanduser()

    if not path.exists():
        raise ValueError(f'файл не найден: {path}')
    if not path.is_file():
        raise ValueError(f'путь не является файлом: {path}')
    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f'файл слишком большой: {path}. Максимум 5 МБ.')

    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError as error:
        raise ValueError(f'файл не является текстовым UTF-8 файлом: {path}') from error
    except OSError as error:
        raise ValueError(f'не удалось прочитать файл: {path}') from error


def _ask_user_prompt() -> str | None:
    print('Принято. Что нужно сделать для каждого фрагмента (User Prompt)?')
    user_prompt = input('> ').strip()
    if user_prompt == QUIT_COMMAND:
        return None
    if not user_prompt:
        raise ValueError('user prompt не должен быть пустым.')

    return user_prompt


def _split_text_into_chunks(file_text: str, options: ChunkOptions) -> list[str]:
    if options.chunk_length is not None:
        return _split_text_by_length(file_text, options.chunk_length)
    return _split_text_by_paragraphs(file_text, options.paragraph_count)


def _split_text_by_length(file_text: str, chunk_length: int) -> list[str]:
    return [
        file_text[start: start + chunk_length]
        for start in range(0, len(file_text), chunk_length)
        if file_text[start: start + chunk_length].strip()
    ]


def _split_text_by_paragraphs(file_text: str, paragraph_count: int) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in file_text.splitlines() if paragraph.strip()]
    chunks = []
    for start in range(0, len(paragraphs), paragraph_count):
        chunks.append('\n'.join(paragraphs[start: start + paragraph_count]))
    return chunks


def _process_chunks(
    chunks: list[str],
    user_prompt: str,
    auto_run: bool,
    config: AppConfig,
) -> None:
    for chunk in chunks:
        if not auto_run:
            user_input = input('> ').strip()
            if user_input == QUIT_COMMAND:
                print('Выход из режима обработки файла.')
                return

        ask_llm_in_filechunk_mode(f'{user_prompt}\n\n{chunk}', config)
        print()

    print('Обработка файла завершена.')
