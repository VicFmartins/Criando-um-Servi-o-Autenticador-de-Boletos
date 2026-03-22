# Servico Autenticador de Boletos

Este repositorio virou uma API executavel para autenticacao de boletos, em vez de ficar apenas no campo conceitual. O projeto agora valida linha digitavel e codigo de barras, diferencia boleto bancario de boleto de arrecadacao, converte entre formatos e retorna metadados uteis para integracao.

## O que o projeto entrega

- API REST em FastAPI
- validacao de boletos bancarios com modulo 10 e modulo 11
- validacao de boletos de arrecadacao com modulo 10 ou modulo 11
- conversao entre linha digitavel e codigo de barras
- endpoint de health check
- rate limiting simples em memoria
- suporte opcional a API key por header
- testes automatizados
- Dockerfile para execucao e deploy basico

## Estrutura

- `app/main.py`: endpoints da API
- `app/validator.py`: regras de validacao e parsing
- `app/security.py`: API key opcional e rate limiting
- `tests/test_validator.py`: cobertura dos cenarios principais
- `examples/sample-request.json`: payload de exemplo

## Endpoints

### `GET /health`

Retorna o status da aplicacao.

### `POST /api/boletos/validate`

Valida um codigo enviado como linha digitavel ou codigo de barras.

Exemplo de corpo:

```json
{
  "code": "00190500954014481606906809350314337370000000100"
}
```

Exemplo de resposta:

```json
{
  "input_code": "00190500954014481606906809350314337370000000100",
  "normalized_code": "00190500954014481606906809350314337370000000100",
  "type": "bank_slip",
  "format": "digitable_line",
  "valid": true,
  "barcode": "00193373700000001000500940144816060680935031",
  "digitable_line": "00190500954014481606906809350314337370000000100",
  "amount": 1.0,
  "due_date": "2007-12-31",
  "bank_code": "001",
  "currency_code": "9",
  "segment_code": null,
  "value_type": null,
  "warning": "Fator de vencimento ambiguo apos 22/02/2025. Outra data possivel: 2032-08-21.",
  "message": "Boleto bancario valido. Banco identificado: Banco do Brasil."
}
```

## Como executar localmente

### Com Python

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Com Docker

```bash
docker build -t boleto-auth .
docker run -p 8000:8000 boleto-auth
```

## Seguranca basica

O projeto inclui dois mecanismos simples para deixar o exemplo mais realista:

- rate limiting em memoria por IP
- API key opcional via header `X-API-Key`

Se a variavel `BOLETO_AUTH_API_KEY` estiver definida, a API passa a exigir esse header.

## Cobertura atual

- validacao de boleto bancario por linha digitavel
- validacao de boleto bancario por codigo de barras
- validacao de boleto de arrecadacao
- rejeicao de digito verificador invalido
- validacao do payload HTTP

## Observacao importante sobre vencimento

O fator de vencimento dos boletos bancarios foi reiniciado em 22/02/2025. Por isso, alguns fatores entre `1000` e `9999` podem representar duas datas possiveis, dependendo da data de emissao. Quando isso acontece, a API retorna uma data principal e inclui um aviso com a data alternativa.

## Referencias

Este projeto foi estruturado com base em documentacoes tecnicas usadas no mercado:

- [Banco do Brasil: Especificacoes Tecnicas para Confeccao de Boleto de Pagamentos](https://www.bb.com.br/docs/pub/emp/empl/dwn/Doc5175Bloqueto.pdf)
- [FEBRABAN: Layout Padrao de Arrecadacao e Recebimento](https://www.febraban.org.br/7Rof7SWg6qmyvwJcFwF7I0aSDf9jyV/sitefebraban/Codbar4-v28052004.pdf)

## Proximos passos

- persistir logs de validacao
- adicionar lista de boletos suspeitos
- integrar observabilidade
- publicar imagem em registry
- adicionar autenticacao JWT para clientes internos
