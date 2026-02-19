
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class MonthItem(BaseModel):
    caminho: str
    display: str
    mes_raw: int

class MonthListResponse(BaseModel):
    data: Dict[str, List[MonthItem]]

class KPIs(BaseModel):
    total_bruto: int
    total_validos: int
    clientes_unicos: int

class MonthDataResponse(BaseModel):
    total_records: int
    columns: List[str]
    records: List[Dict[str, Any]]
    kpis: KPIs


class PeriodRequest(BaseModel):
    months: List[str] # ["2026_01", "2026_02"]


class HealthResponse(BaseModel):
    status: str
    bigquery: bool

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_role: str

class RegisterClientRequest(BaseModel):
    nome_contato: str
    nome_cliente: str

class RegisterClientResponse(BaseModel):
    success: bool
    message: str


class UploadMonthResponse(BaseModel):
    success: bool
    message: str
    filename: str

class LabelRequest(BaseModel):
    label: str

class LabelResponse(BaseModel):
    success: bool
    message: str
    storage: str

class LabelsListResponse(BaseModel):
    labels: Dict[str, str]




