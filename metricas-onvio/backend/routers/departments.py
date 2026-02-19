
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from backend.services.departments_service import load_departments, update_single_analyst
from backend.services.data_service import listar_arquivos_por_ano, carregar_dados_mes

router = APIRouter(prefix="/api/departments", tags=["departments"])

class DepartmentUpdate(BaseModel):
    analyst: str
    department: str

@router.get("", response_model=Dict[str, str])
def get_departments():
    """Retorna o mapeamento atual de analistas para departamentos."""
    return load_departments()

@router.post("")
def update_department(data: DepartmentUpdate):
    """Atualiza o departamento de um analista."""
    success = update_single_analyst(data.analyst, data.department)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao salvar departamento")
    return {"status": "ok", "analyst": data.analyst, "department": data.department}

@router.get("/analysts", response_model=List[str])
def get_all_analysts():
    """Retorna lista única de todos os analistas encontrados em todos os meses disponíveis."""
    analysts = set()
    structure = listar_arquivos_por_ano()
    
    # Flatten structure to get list of all months
    all_months = []
    for year_data in structure.values():
        all_months.extend(year_data)
        
    for month in all_months:
        try:
            # Load data for the month
            df = carregar_dados_mes(month["caminho"])
            if df is not None and "Atendido por" in df.columns:
                # Extract unique names, convert to string, uppercase, add to set
                names = df["Atendido por"].dropna().astype(str).str.strip().str.upper().unique()
                analysts.update(names)
        except Exception:
            continue
            
    return sorted(list(analysts))
