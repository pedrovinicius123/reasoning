from axle import AxleClient
from axle.exceptions import AxleApiError  # Importe a classe base de erro da API
from dotenv import load_dotenv

import re

load_dotenv()


def extract_formal_statement(lean_code: str) -> str:
    """
    Pega a primeira declaração `theorem NOME ... := by ...` do código,
    terminando com `:= by sorry` (placeholder para o Axle).
    Se não achar, retorna o próprio código como fallback.
    """
    m = re.search(
        r"(theorem\s+\w+.*?:=\s*by)",
        lean_code,
        re.DOTALL,
    )
    if not m:
        return lean_code
    stmt = m.group(1).strip()
    if "sorry" not in stmt:
        stmt = stmt + " sorry"
    return stmt


async def verify_proof(formal_statement:str, lean_code: str) -> dict:
    try:
        async with AxleClient() as client:
            result = await client.verify_proof(  # <- não `check`
                formal_statement=formal_statement,
                content=lean_code,
                environment="lean-4.28.0",
            )
            errors = []
            if result.lean_messages and result.lean_messages.errors:
                errors = [str(e) for e in result.lean_messages.errors]

            return {
                "verified": result.okay,
                "sorries": getattr(result, "sorries", []) or [],
                "proof_errors": result.tool_messages.errors or [],
                "failed_declarations": result.failed_declarations or [],
                "errors": errors,
                "raw": result,
            }
    except AxleApiError as e:
        return {"verified": False, "sorries": [], "failed_declarations": [],
                "errors": [f"Erro na API AXLE: {e}"], "raw": None}
    except Exception as e:
        return {"verified": False, "sorries": [], "failed_declarations": [],
                "errors": [f"Erro inesperado: {e}"], "raw": None}