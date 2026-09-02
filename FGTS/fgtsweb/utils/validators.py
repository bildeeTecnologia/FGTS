import re
import unicodedata
from typing import Optional, Dict

import requests
from django.core.exceptions import ValidationError


ASCII_SPACE_PATTERN = re.compile(r"\s+")


def digits_only(value: Optional[str]) -> str:
    """Return only numeric characters from a string."""
    if value is None:
        return ""
    return re.sub(r"\D", "", str(value))


def normalize_upper_ascii(value: Optional[str], *, allow_digits: bool = True, allow_spaces: bool = True) -> str:
    """Uppercase text, strip accents and drop special characters.

    Only letters are always allowed. Digits and spaces are optional.
    Multiple spaces are collapsed. Returns empty string for falsy values.
    """
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.upper()

    cleaned_chars = []
    for ch in text:
        if ch.isalpha():
            cleaned_chars.append(ch)
        elif allow_digits and ch.isdigit():
            cleaned_chars.append(ch)
        elif allow_spaces and ch.isspace():
            cleaned_chars.append(" ")
        # All other characters are dropped to avoid special characters

    cleaned = "".join(cleaned_chars)
    cleaned = ASCII_SPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned


def validate_cpf(value: Optional[str]) -> str:
    """Validate a CPF and return the normalized numeric string."""
    cpf = digits_only(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError("CPF invalido. Informe 11 digitos validos.")

    for idx in range(9, 11):
        weight = list(range(idx + 1, 1, -1))
        total = sum(int(cpf[i]) * weight[i] for i in range(idx))
        digit = (total * 10) % 11
        digit = 0 if digit == 10 else digit
        if digit != int(cpf[idx]):
            raise ValidationError("CPF invalido. Confira os digitos verificadores.")
    return cpf


def validate_pis(value: Optional[str]) -> str:
    """Validate a PIS/NIS number and return the numeric string."""
    pis = digits_only(value)
    if not pis:
        return ""
    if len(pis) != 11 or pis == pis[0] * 11:
        raise ValidationError("PIS/NIS invalido. Informe 11 digitos validos.")

    weights = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(pis[i]) * weights[i] for i in range(10))
    remainder = total % 11
    check_digit = 0 if remainder < 2 else 11 - remainder
    if check_digit != int(pis[10]):
        raise ValidationError("PIS/NIS invalido. Confira os digitos verificadores.")
    return pis


def validate_cep(value: Optional[str]) -> str:
    """Validate a CEP and return the numeric string."""
    cep = digits_only(value)
    if not cep:
        return ""
    if len(cep) != 8:
        raise ValidationError("CEP invalido. Use 8 digitos.")
    return cep


def fetch_cep_data(cep: str, *, timeout: int = 5) -> Dict[str, str]:
    """Query ViaCEP and return sanitized address fields.

    Raises ValidationError when the CEP is not found or the service fails.
    """
    cep = validate_cep(cep)
    if not cep:
        raise ValidationError("CEP nao informado.")

    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        raise ValidationError(f"Nao foi possivel consultar o CEP agora: {exc}")

    if response.status_code != 200:
        raise ValidationError("Servico de CEP indisponivel no momento.")

    data = response.json()
    if data.get("erro"):
        raise ValidationError("CEP nao encontrado na base dos Correios.")

    endereco = normalize_upper_ascii(data.get("logradouro", ""), allow_digits=True)
    bairro = normalize_upper_ascii(data.get("bairro", ""), allow_digits=True)
    cidade = normalize_upper_ascii(data.get("localidade", ""), allow_digits=False)
    uf = normalize_upper_ascii(data.get("uf", ""), allow_digits=False)

    return {
        "endereco": endereco,
        "bairro": bairro,
        "cidade": cidade,
        "uf": uf,
        "cep": cep,
    }
