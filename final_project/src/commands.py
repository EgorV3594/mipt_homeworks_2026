from dataclasses import dataclass
from typing import Callable

from src.config import AppConfig
from src.file_chunk import run_file_chunk_mode
from src.llm import ask_llm, reset_chat, show_chat_history


@dataclass(frozen=True)
class Command:
    description: str
    handler: Callable[[list[str], AppConfig], bool]


def handle_help_command(args: list[str], config: AppConfig) -> bool:
    _ = config

    if args:
        print('Команда /help не принимает аргументы.')
    print('Доступные команды:')
    for command_name, command in COMMANDS.items():
        print(f'{command_name} - {command.description}')
    print('Чтобы добавить файл к запаросу используйте @::path/exmaple.txt::')
    return True


def handle_exit_command(args: list[str], config: AppConfig) -> bool:
    _ = config

    if args:
        print('Команда выхода не принимает аргументы.')

    print('Выход из приложения.')
    return False


def handle_message(message: str, config: AppConfig) -> bool:
    try:
        ask_llm(message, config)
        print()
    except KeyboardInterrupt:
        print('\nЗапрос к модели прерван.')
    except ValueError as error:
        print(f'Ошибка конфигурации: {error}')
    except RuntimeError as error:
        print(f'Ошибка обращения к LLM: {error}')

    return True


def handle_command(command_name: str, args: list[str], config: AppConfig) -> bool:
    command = COMMANDS.get(command_name)

    if command is None:
        print(f'Неизвестная команда: {command_name}')
        print('Напишите /help, чтобы увидеть список доступных команд.')
        return True

    return command.handler(args, config)


COMMANDS = {
    '/help': Command(
        description='показать список команд',
        handler=handle_help_command,
    ),
    '/exit': Command(
        description='выйти из приложения',
        handler=handle_exit_command,
    ),
    '/quit': Command(
        description='выйти из приложения',
        handler=handle_exit_command,
    ),
    '\\q': Command(
        description='выйти из приложения, когда включен режим filechunk выходит только из него',
        handler=handle_exit_command,
    ),
    '/reset': Command(
        description='очистить историю сообщений',
        handler=reset_chat,
    ),
    '/history': Command(
        description='показать текущую историю сообщений',
        handler=show_chat_history,
    ),
    '/file_chunk': Command(
        description='запустить обработку файла по частям',
        handler=run_file_chunk_mode,
    ),
}
