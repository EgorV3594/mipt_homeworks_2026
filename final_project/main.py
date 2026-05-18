from dataclasses import dataclass

from src.commands import handle_command, handle_message
from src.config import AppConfig, load_config


@dataclass(frozen=True)
class ParsedInput:
    type: str
    value: str
    args: list[str]


def parse_user_input(user_input: str) -> ParsedInput:
    user_input = user_input.strip()
    if not user_input:
        return ParsedInput(type='empty', value='', args=[])
    if user_input.startswith('/') or user_input == '\\q':
        command, *args = user_input.split()
        return ParsedInput(type='command', value=command.lower(), args=args)

    return ParsedInput(type='message', value=user_input, args=[])


def run_chat_loop(config: AppConfig) -> None:
    print('Консольный ассистент запущен. Напишите /help для списка команд.')

    while True:
        try:
            user_input = input('> ')
        except (EOFError, KeyboardInterrupt):
            print('\nВыход из приложения.')
            break

        parsed_input = parse_user_input(user_input)

        if parsed_input.type == 'empty':
            continue

        if parsed_input.type == 'message':
            should_continue = handle_message(parsed_input.value, config)
        else:
            should_continue = handle_command(parsed_input.value, parsed_input.args, config)

        if not should_continue:
            break


def main() -> None:
    try:
        config = load_config()
    except ValueError as error:
        print(f'Ошибка конфигурации: {error}')
        return

    run_chat_loop(config)


if __name__ == '__main__':
    main()
