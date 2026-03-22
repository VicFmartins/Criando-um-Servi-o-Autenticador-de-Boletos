from fastapi.testclient import TestClient

from app.main import app
from app.validator import (
    arrecadacao_barcode_to_digitable_line,
    bank_barcode_to_digitable_line,
    modulo10,
    validate_boleto,
)


client = TestClient(app)

BANK_BARCODE = "00193373700000001000500940144816060680935031"
BANK_DIGITABLE_LINE = "00190500954014481606906809350314337370000000100"
ARRECADACAO_FREE_FIELD = "0000001234567890123456789012345678901234"
ARRECADACAO_BARCODE = f"816{modulo10('816' + ARRECADACAO_FREE_FIELD)}{ARRECADACAO_FREE_FIELD}"


def test_validate_bank_barcode() -> None:
    result = validate_boleto(BANK_BARCODE)

    assert result.valid is True
    assert result.type == "bank_slip"
    assert result.amount == 1.0
    assert result.bank_code == "001"
    assert result.digitable_line == BANK_DIGITABLE_LINE


def test_validate_bank_digitable_line() -> None:
    result = validate_boleto(BANK_DIGITABLE_LINE)

    assert result.valid is True
    assert result.format == "digitable_line"
    assert result.barcode == BANK_BARCODE
    assert result.warning is not None


def test_validate_arrecadacao_barcode_and_line() -> None:
    digitable_line = arrecadacao_barcode_to_digitable_line(ARRECADACAO_BARCODE)

    barcode_result = validate_boleto(ARRECADACAO_BARCODE)
    line_result = validate_boleto(digitable_line)

    assert barcode_result.type == "collection"
    assert barcode_result.barcode == ARRECADACAO_BARCODE
    assert line_result.barcode == ARRECADACAO_BARCODE
    assert line_result.digitable_line == digitable_line


def test_invalid_bank_dv_is_rejected() -> None:
    invalid = BANK_DIGITABLE_LINE[:-1] + "9"

    response = client.post("/api/boletos/validate", json={"code": invalid})

    assert response.status_code == 422
    assert "Digito verificador" in response.json()["detail"]


def test_api_returns_valid_payload() -> None:
    response = client.post("/api/boletos/validate", json={"code": BANK_DIGITABLE_LINE})

    assert response.status_code == 200
    payload = response.json()
    assert payload["barcode"] == BANK_BARCODE
    assert payload["valid"] is True
    assert payload["warning"] is not None


def test_helper_generates_expected_bank_digitable_line() -> None:
    assert bank_barcode_to_digitable_line(BANK_BARCODE) == BANK_DIGITABLE_LINE
