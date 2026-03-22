from fastapi import Depends, FastAPI, HTTPException

from app.models import ValidationRequest, ValidationResponse
from app.security import api_key_dependency, rate_limit_dependency
from app.validator import validate_boleto


app = FastAPI(
    title="Boleto Auth Service",
    version="1.0.0",
    description="API para autenticacao e validacao de boletos bancarios e de arrecadacao.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "boleto-auth"}


@app.post(
    "/api/boletos/validate",
    response_model=ValidationResponse,
    dependencies=[Depends(rate_limit_dependency), Depends(api_key_dependency)],
)
def validate_boleto_endpoint(payload: ValidationRequest) -> ValidationResponse:
    try:
        result = validate_boleto(payload.code)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return ValidationResponse(**result.__dict__)
