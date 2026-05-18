from typing import Any, cast
from openai import OpenAI, OpenAIError

from src.expanding_references import expand_references
from src.config import AppConfig


Message = dict[str, str]


CHAT_HISTORY: list[Message] = []


def ask_llm(message: str, config: AppConfig) -> str:
    message = expand_references(message)
    limited_message = _apply_context_limits(message, config)
    messages = _build_messages(limited_message, config)
    answer = _send_messages_to_llm(messages, config)

    CHAT_HISTORY.append({'role': 'user', 'content': limited_message})
    CHAT_HISTORY.append({'role': 'assistant', 'content': answer})

    return answer


def ask_llm_in_filechunk_mode(message: str, config: AppConfig) -> str:
    messages: list[Message] = []
    if config.system_prompt:
        messages.append({'role': 'system', 'content': config.system_prompt})
    messages.append({'role': 'user', 'content': message})
    return _send_messages_to_llm(messages, config)


def _send_messages_to_llm(messages: list[Message], config: AppConfig) -> str:
    client = OpenAI(
        api_key=config.api_key,
        base_url=config.api_host,
    )
    answer_parts = []

    try:
        stream = client.chat.completions.create(
            model=config.model,
            messages=cast(Any, messages),
            stream=True,
            temperature=config.temperature,
        )

        for chunk in stream:
            text_part = chunk.choices[0].delta.content
            if text_part is None:
                continue
            print(text_part, end='', flush=True)
            answer_parts.append(text_part)

    except OpenAIError as error:
        raise RuntimeError(str(error)) from error

    return ''.join(answer_parts)


def _apply_context_limits(message: str, config: AppConfig) -> str:
    if config.limit_chars is not None and len(message) > config.limit_chars:
        message = message[-config.limit_chars:]

    if config.limit_message is not None:
        while len(CHAT_HISTORY) + 1 > config.limit_message and CHAT_HISTORY:
            CHAT_HISTORY.pop(0)

    if config.limit_chars is not None:
        _apply_chars_limits(config.limit_chars, len(message))

    return message


def _apply_chars_limits(limit_chars: int, extra_chars: int = 0) -> None:
    chars_to_remove = _count_history_chars() + extra_chars - limit_chars

    while chars_to_remove > 0 and CHAT_HISTORY:
        oldest_message = CHAT_HISTORY[0]
        oldest_content = oldest_message['content']

        if len(oldest_content) <= chars_to_remove:
            CHAT_HISTORY.pop(0)
            chars_to_remove -= len(oldest_content)
            continue

        oldest_message['content'] = oldest_content[chars_to_remove:]
        chars_to_remove = 0


def _count_history_chars() -> int:
    return sum(len(message['content']) for message in CHAT_HISTORY)


def _build_messages(message: str, config: AppConfig) -> list[Message]:
    messages: list[Message] = []
    if config.system_prompt:
        messages.append({'role': 'system', 'content': config.system_prompt})

    messages.extend(CHAT_HISTORY)
    messages.append({'role': 'user', 'content': message})
    return messages


def reset_chat(args: list[str], config: AppConfig) -> bool:
    _ = config

    if args:
        print('Команда /reset не принимает аргументы.')

    CHAT_HISTORY.clear()
    print('История чата очищена.')
    return True


def show_chat_history(args: list[str], config: AppConfig) -> bool:
    _ = config

    if args:
        print('Команда /history не принимает аргументы.')

    if not CHAT_HISTORY:
        print('История чата пуста.')
        return True

    for message_number, message in enumerate(CHAT_HISTORY, start=1):
        print(f'{message_number}. {message["role"]}: {message["content"]}')

    return True
