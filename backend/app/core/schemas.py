from pydantic import BaseModel, Field
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

class ProcessRequest(BaseModel):
    """
    Define os parâmetros que podem ser enviados ao iniciar um processo de análise.
    Valores padrão são fornecidos para todos os campos.
    """
    fps: float = Field(default=1.0, gt=0, le=30) # Frequência de frames por segundo
    similarity_threshold: float = Field(default=0.4, gt=0, lt=1.0) # Limiar de similaridade
    batch_size: int = Field(default=32, gt=0, le=128) # Tamanho do lote para a GPU