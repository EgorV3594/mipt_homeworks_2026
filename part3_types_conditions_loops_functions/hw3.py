#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"
INCOME = "income"
COST = "cost"
STATS = "stats"
KEY_TYPE = "type"
KEY_AMOUNT = "amount"
KEY_DATE = "date"
KEY_CATEGORY = "categories"


number_of_date_parts = 3
number_of_month = 12
days_in_other_montth = [30, 31]
days_in_februaty = [28, 29]
income_querry_parts = 3
cost_querry_parts = 4
categories_querry_parts = 4
stats_querry_parts = 2
DateTuple = tuple[int, int, int]

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    if year % 4 != 0:
        return False
    if year % 100 != 0:
        return True
    return year % 400 == 0


def days_in_month(month: int, year: int) -> int:
    if month in (1, 3, 5, 7, 8, 10, 12):
        return days_in_other_montth[1]
    if month in (4, 6, 9, 11):
        return days_in_other_montth[0]
    if is_leap_year(year):
        return days_in_februaty[1]
    return days_in_februaty[0]


def extract_date(date_str: str) -> tuple[int, int, int] | None:
    parts = date_str.split("-")
    if len(parts) != number_of_date_parts:
        return None

    if not all(x.isdigit() for x in parts):
        return None

    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])

    if year <= 0 or not (1 <= month <= number_of_month):
        return None

    if day < 1 or day > days_in_month(month, year):
        return None

    return day, month, year


def category_exists(category_name: str) -> bool:
    if "::" not in category_name:
        return False
    common, target = category_name.split("::", 1)
    if common not in EXPENSE_CATEGORIES:
        return False
    return target in EXPENSE_CATEGORIES[common]


def cost_categories_handler() -> str:
    return "\n".join(
        f"{k}::{v}"
        for k, kv in EXPENSE_CATEGORIES.items()
        for v in kv
    )


def date_loweq(d1: DateTuple, d2: DateTuple) -> bool:
    if d1[2] != d2[2]:
        return d1[2] < d2[2]
    if d1[1] != d2[1]:
        return d1[1] < d2[1]
    return d1[0] <= d2[0]


def one_month(d1: DateTuple, d2: DateTuple) -> bool:
    same_month = d1[1] == d2[1]
    same_year = d1[2] == d2[2]
    return same_month and same_year


def update_totals_for_income(
    item: dict[str, Any],
    report: DateTuple,
    total_capital: float,
    month_income: float,
) -> tuple[float, float]:
    item_date = item[KEY_DATE]
    if not one_month(item_date, report):
        return total_capital + item[KEY_AMOUNT], month_income
    total_capital += item[KEY_AMOUNT]
    month_income += item[KEY_AMOUNT]
    return total_capital, month_income


def update_totals_for_cost(
    item: dict[str, Any],
    report: DateTuple,
    total_capital: float,
    month_expenses: float,
    expenses_by_cat: dict[str, float],
) -> tuple[float, float]:
    item_date = item[KEY_DATE]
    total_capital -= item[KEY_AMOUNT]
    if one_month(item_date, report):
        month_expenses += item[KEY_AMOUNT]
        cat = item[KEY_CATEGORY]
        expenses_by_cat[cat] = expenses_by_cat.get(cat, 0) + item[KEY_AMOUNT]
    return total_capital, month_expenses


def aggregate_stats(
    report_tuple: DateTuple,
) -> tuple[float, float, float, dict[str, float]]:
    total_capital: float = 0
    month_income: float = 0
    month_expenses: float = 0
    expenses_by_cat: dict[str, float] = {}

    for item in financial_transactions_storage:
        if not date_loweq(item[KEY_DATE], report_tuple):
            continue

        if item[KEY_TYPE] == INCOME:
            total_capital, month_income = update_totals_for_income(
                item, report_tuple, total_capital, month_income,
            )
        elif item[KEY_TYPE] == COST:
            total_capital, month_expenses = update_totals_for_cost(
                item, report_tuple, total_capital, month_expenses, expenses_by_cat,
            )

    return total_capital, month_income, month_expenses, expenses_by_cat


def profit_or_loss(month_income: float, month_expenses: float) -> str:
    diff = month_income - month_expenses
    if diff >= 0:
        return f"This month, the profit amounted to {diff:.2f} rubles."
    return f"This month, the loss amounted to {abs(diff):.2f} rubles."


def format_stats(expenses_by_categorie: dict[str, float]) -> list[str]:
    lines: list[str] = []
    lines.append("Details (category: amount):")
    if expenses_by_categorie:
        sorted_items = sorted(expenses_by_categorie.items(), key=lambda x: x[0])
        for idx, (cat, amount) in enumerate(sorted_items, start=1):
            lines.append(f"{idx}. {cat}: {amount:.2f}")
    return lines


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {
            KEY_TYPE: INCOME,
            KEY_AMOUNT: amount,
            KEY_DATE: parsed_date,
        }
    )
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    if not category_exists(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    financial_transactions_storage.append(
        {
            KEY_TYPE: COST,
            KEY_CATEGORY: category_name,
            KEY_AMOUNT: amount,
            KEY_DATE: parsed_date,
        }
    )
    return OP_SUCCESS_MSG


def stats_handler(report_date: str) -> str:
    report_d = extract_date(report_date)
    if report_d is None:
        return INCORRECT_DATE_MSG

    stats = aggregate_stats(report_d)

    lines: list[str] = []
    lines.append(f"Your statistics as of {report_date}:")
    lines.append(f"Total capital: {stats[0]:.2f} rubles")
    lines.append(profit_or_loss(stats[1], stats[2]))
    lines.append(f"Income: {stats[1]:.2f} rubles")
    lines.append(f"Expenses: {stats[2]:.2f} rubles")
    lines.append("")
    lines.extend(format_stats(stats[3]))
    return "\n".join(lines)


def handle_income_command(parts: list[str]) -> str:
    if len(parts) != income_querry_parts:
        return UNKNOWN_COMMAND_MSG

    amount_str = parts[1]
    date_str = parts[2]

    amount = float(amount_str)
    return income_handler(amount, date_str)


def handle_cost_add_command(parts: list[str]) -> str:
    if len(parts) != cost_querry_parts:
        return UNKNOWN_COMMAND_MSG

    category_name = parts[1]
    amount_str = parts[2]
    date_str = parts[3]

    amount = float(amount_str)
    result = cost_handler(category_name, amount, date_str)
    if result == NOT_EXISTS_CATEGORY:
        return f"{NOT_EXISTS_CATEGORY}\n{cost_categories_handler()}"
    return result


def handle_stats_command(parts: list[str]) -> str:
    if len(parts) != stats_querry_parts:
        return UNKNOWN_COMMAND_MSG
    date_str = parts[1]
    return stats_handler(date_str)


def command_handler(command: str, parts: list[str]) -> str | None:
    if command == INCOME:
        return handle_income_command(parts)
    is_cost_command = command == COST
    has_categories_len = len(parts) == categories_querry_parts
    is_categories_subcommand = parts[1] == KEY_CATEGORY

    if is_cost_command and has_categories_len and is_categories_subcommand:
        return cost_categories_handler()

    if command == COST:
        return handle_cost_add_command(parts)

    if command == STATS:
        return handle_stats_command(parts)
    return None


def process_command(line: str) -> str | None:
    if not line:
        return None
    parts = line.split()
    result = command_handler(parts[0], parts)
    if result is not None:
        return result
    return UNKNOWN_COMMAND_MSG


def main() -> None:
    line = input().strip()
    while line:
        result = process_command(line)
        if result:
            print(result)
        line = input().strip()


if __name__ == "__main__":
    main()
