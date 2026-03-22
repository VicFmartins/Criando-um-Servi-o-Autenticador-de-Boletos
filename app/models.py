from pydantic import BaseModel, Field


class ValidationRequest(BaseModel):
    code: str = Field(min_length=44, max_length=60, description="Linha digitavel ou codigo de barras")


class ValidationResponse(BaseModel):
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
