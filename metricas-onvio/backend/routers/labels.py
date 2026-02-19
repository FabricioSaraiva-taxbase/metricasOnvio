"""
Router de Labels de Meses.
GET  /api/labels → lista todas as labels.
PUT  /api/labels/{mes_key} → cria/atualiza label.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.auth import require_admin, get_current_user
from backend.models.schemas import LabelRequest, LabelResponse, LabelsListResponse
from backend.services.labels_service import load_month_labels, save_month_label

router = APIRouter(prefix="/api/labels", tags=["Labels"])


@router.get("", response_model=LabelsListResponse)
async def get_labels(current_user: dict = Depends(get_current_user)):
    """Retorna todas as labels de meses configuradas."""
    try:
        labels = load_month_labels()
        return LabelsListResponse(labels=labels)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar labels: {str(e)}",
        )


@router.put("/{mes_key}", response_model=LabelResponse)
async def set_label(
    mes_key: str,
    request: LabelRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Cria ou atualiza a label de um mês.
    Para remover, envie label vazio.
    Restrito a administradores.
    """
    sucesso, storage = save_month_label(mes_key, request.label)

    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar label: {storage}",
        )

    return LabelResponse(
        success=True,
        message=f"Label {'atualizada' if request.label.strip() else 'removida'} com sucesso!",
        storage=storage,
    )
