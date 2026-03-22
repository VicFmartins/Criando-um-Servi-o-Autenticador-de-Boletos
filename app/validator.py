from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


BANK_CODE_NAMES = {
    "001": "Banco do Brasil",
    "033": "Santander",
    "104": "Caixa Economica Federal",
    "237": "Bradesco",
    "341": "Itau",
    "748": "Sicredi",
    "756": "Sicoob",
}

BANK_DUE_DATE_BASE = date(1997, 10, 7)
BANK_DUE_DATE_RESET_BASE = date(2025, 2, 22)


@dataclass
class ValidationResult:
    input_code: str
    normalized_code: str
    type: str
    format: str
    valid: bool
    barcode: str
    digitable_line: str | None
    amount: float | None
    due_date: str | None
    bank_code: str | None
    currency_code: str | None
    segment_code: str | None
    value_type: str | None
    warning: str | None
    message: str


def only_digits(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def modulo10(number: str) -> int:
    total = 0
    multiplier = 2
    for digit in reversed(number):
        partial = int(digit) * multiplier
        total += partial if partial < 10 else sum(int(n) for n in str(partial))
        multiplier = 1 if multiplier == 2 else 2
    remainder = total % 10
    return 0 if remainder == 0 else 10 - remainder


def modulo11_bank(number: str) -> int:
    total = 0
    weight = 2
    for digit in reversed(number):
        total += int(digit) * weight
        weight = 2 if weight == 9 else weight + 1
    remainder = total % 11
    digit = 11 - remainder
    return 1 if digit in {0, 10, 11} else digit


def modulo11_arrecadacao(number: str) -> int:
    total = 0
    weight = 2
    for digit in reversed(number):
        total += int(digit) * weight
        weight = 2 if weight == 9 else weight + 1
    remainder = total % 11
    if remainder in {0, 1}:
        return 0
    if remainder == 10:
        return 1
    return 11 - remainder


def bank_factor_to_due_date(factor: str) -> tuple[str | None, str | None]:
    if factor == "0000":
        return None, None
    factor_number = int(factor)
    legacy_candidate = BANK_DUE_DATE_BASE + timedelta(days=factor_number)
    if 1000 <= factor_number <= 9999 and legacy_candidate <= date(2025, 2, 21):
        reset_candidate = BANK_DUE_DATE_RESET_BASE + timedelta(days=factor_number - 1000)
        return (
            legacy_candidate.isoformat(),
            f"Fator de vencimento ambiguo apos 22/02/2025. Outra data possivel: {reset_candidate.isoformat()}.",
        )
    return legacy_candidate.isoformat(), None


def amount_from_cents(value_digits: str) -> float | None:
    if set(value_digits) == {"0"}:
        return 0.0
    return int(value_digits) / 100


def bank_barcode_to_digitable_line(barcode: str) -> str:
    field1 = barcode[0:4] + barcode[19:24]
    field2 = barcode[24:34]
    field3 = barcode[34:44]
    field4 = barcode[4]
    field5 = barcode[5:19]
    return (
        f"{field1}{modulo10(field1)}"
        f"{field2}{modulo10(field2)}"
        f"{field3}{modulo10(field3)}"
        f"{field4}{field5}"
    )


def bank_digitable_line_to_barcode(digitable_line: str) -> str:
    return (
        digitable_line[0:4]
        + digitable_line[32]
        + digitable_line[33:47]
        + digitable_line[4:9]
        + digitable_line[10:20]
        + digitable_line[21:31]
    )


def arrecadacao_barcode_to_digitable_line(barcode: str) -> str:
    algorithm = get_arrecadacao_algorithm(barcode)
    segments = [barcode[index : index + 11] for index in range(0, 44, 11)]
    verifier = modulo10 if algorithm == "mod10" else modulo11_arrecadacao
    return "".join(f"{segment}{verifier(segment)}" for segment in segments)


def arrecadacao_digitable_line_to_barcode(digitable_line: str) -> str:
    parts = [digitable_line[index : index + 12] for index in range(0, 48, 12)]
    return "".join(part[:11] for part in parts)


def get_arrecadacao_algorithm(code: str) -> str:
    identifier = code[2]
    if identifier in {"6", "7"}:
        return "mod10"
    if identifier in {"8", "9"}:
        return "mod11"
    raise ValueError("Codigo de arrecadacao invalido: identificador de valor desconhecido.")


def get_arrecadacao_value_type(code: str) -> str:
    identifier = code[2]
    if identifier in {"6", "8"}:
        return "effective"
    if identifier in {"7", "9"}:
        return "reference"
    raise ValueError("Codigo de arrecadacao invalido: identificador de valor desconhecido.")


def validate_bank_barcode(barcode: str) -> ValidationResult:
    if len(barcode) != 44 or not barcode.isdigit():
        raise ValueError("Codigo de barras bancario deve ter 44 digitos.")

    expected_dv = modulo11_bank(barcode[:4] + barcode[5:])
    if barcode[4] != str(expected_dv):
        raise ValueError("Digito verificador geral do codigo de barras bancario invalido.")

    amount_digits = barcode[9:19]
    factor = barcode[5:9]
    due_date, warning = bank_factor_to_due_date(factor)
    digitable_line = bank_barcode_to_digitable_line(barcode)
    bank_code = barcode[:3]

    return ValidationResult(
        input_code=barcode,
        normalized_code=barcode,
        type="bank_slip",
        format="barcode",
        valid=True,
        barcode=barcode,
        digitable_line=digitable_line,
        amount=amount_from_cents(amount_digits),
        due_date=due_date,
        bank_code=bank_code,
        currency_code=barcode[3],
        segment_code=None,
        value_type=None,
        warning=warning,
        message="Boleto bancario valido.",
    )


def validate_bank_digitable_line(digitable_line: str) -> ValidationResult:
    if len(digitable_line) != 47 or not digitable_line.isdigit():
        raise ValueError("Linha digitavel bancaria deve ter 47 digitos.")

    fields = [
        (digitable_line[0:9], digitable_line[9]),
        (digitable_line[10:20], digitable_line[20]),
        (digitable_line[21:31], digitable_line[31]),
    ]
    for field, dv in fields:
        if str(modulo10(field)) != dv:
            raise ValueError("Digito verificador de um dos campos da linha digitavel bancaria e invalido.")

    barcode = bank_digitable_line_to_barcode(digitable_line)
    result = validate_bank_barcode(barcode)
    result.input_code = digitable_line
    result.normalized_code = digitable_line
    result.format = "digitable_line"
    return result


def validate_arrecadacao_barcode(barcode: str) -> ValidationResult:
    if len(barcode) != 44 or not barcode.isdigit() or not barcode.startswith("8"):
        raise ValueError("Codigo de barras de arrecadacao deve ter 44 digitos e iniciar com 8.")

    algorithm = get_arrecadacao_algorithm(barcode)
    value_type = get_arrecadacao_value_type(barcode)
    verifier = modulo10 if algorithm == "mod10" else modulo11_arrecadacao
    expected_dv = verifier(barcode[:3] + barcode[4:])

    if barcode[3] != str(expected_dv):
        raise ValueError("Digito verificador geral do codigo de barras de arrecadacao invalido.")

    amount = amount_from_cents(barcode[4:15]) if value_type == "effective" else None

    return ValidationResult(
        input_code=barcode,
        normalized_code=barcode,
        type="collection",
        format="barcode",
        valid=True,
        barcode=barcode,
        digitable_line=arrecadacao_barcode_to_digitable_line(barcode),
        amount=amount,
        due_date=None,
        bank_code=None,
        currency_code=None,
        segment_code=barcode[1],
        value_type=value_type,
        warning=None,
        message="Boleto de arrecadacao valido.",
    )


def validate_arrecadacao_digitable_line(digitable_line: str) -> ValidationResult:
    if len(digitable_line) != 48 or not digitable_line.isdigit() or not digitable_line.startswith("8"):
        raise ValueError("Linha digitavel de arrecadacao deve ter 48 digitos e iniciar com 8.")

    barcode = arrecadacao_digitable_line_to_barcode(digitable_line)
    algorithm = get_arrecadacao_algorithm(barcode)
    verifier = modulo10 if algorithm == "mod10" else modulo11_arrecadacao

    for index in range(0, 48, 12):
        field = digitable_line[index : index + 11]
        dv = digitable_line[index + 11]
        if str(verifier(field)) != dv:
            raise ValueError("Digito verificador de um dos campos da linha digitavel de arrecadacao e invalido.")

    result = validate_arrecadacao_barcode(barcode)
    result.input_code = digitable_line
    result.normalized_code = digitable_line
    result.format = "digitable_line"
    return result


def validate_boleto(code: str) -> ValidationResult:
    digits = only_digits(code)
    if len(digits) == 47:
        result = validate_bank_digitable_line(digits)
    elif len(digits) == 44 and digits.startswith("8"):
        result = validate_arrecadacao_barcode(digits)
    elif len(digits) == 44:
        result = validate_bank_barcode(digits)
    elif len(digits) == 48 and digits.startswith("8"):
        result = validate_arrecadacao_digitable_line(digits)
    else:
        raise ValueError("Formato nao suportado. Informe 44, 47 ou 48 digitos validos.")

    if result.bank_code in BANK_CODE_NAMES:
        result.message = f"{result.message} Banco identificado: {BANK_CODE_NAMES[result.bank_code]}."
    return result
