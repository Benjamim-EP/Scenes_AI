from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    """
    Define a estrutura dos dados que esperamos receber do frontend
    para uma requisição de busca.
    """
    # Optional[] significa que o campo não é obrigatório
    include_tags: Optional[List[str]] = []
    exclude_tags: Optional[List[str]] = []
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    sort_by: Optional[str] = 'score' # Padrão para ordenar por score da tag (relevância)
    page: int = 1
    limit: int = 24