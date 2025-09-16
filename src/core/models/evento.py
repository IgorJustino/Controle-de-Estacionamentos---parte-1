"""
Modelo de dados para eventos do sistema de estacionamento.
"""
from datetime import datetime
from enum import Enum
from typing import Optional


class TipoEvento(Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    ERRO = "erro"
    MANUTENCAO = "manutencao"


class StatusEvento(Enum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    CONCLUIDO = "concluido"
    ERRO = "erro"


class Evento:
    """Modelo de evento do sistema."""
    
    def __init__(
        self,
        placa: str,
        tipo: TipoEvento,
        timestamp: datetime,
        confianca_lpr: float,
        andar: str = "terreo",
        status: StatusEvento = StatusEvento.PENDENTE,
        id: Optional[str] = None,
        valor_calculado: Optional[float] = None,
        tempo_permanencia_minutos: Optional[int] = None,
        erro_descricao: Optional[str] = None
    ):
        self.id = id
        self.placa = placa
        self.tipo = tipo
        self.timestamp = timestamp
        self.confianca_lpr = confianca_lpr
        self.andar = andar
        self.status = status
        self.valor_calculado = valor_calculado
        self.tempo_permanencia_minutos = tempo_permanencia_minutos
        self.erro_descricao = erro_descricao
    
    def to_dict(self) -> dict:
        """Converte o evento para dicionário."""
        return {
            "id": self.id,
            "placa": self.placa,
            "tipo": self.tipo.value,
            "timestamp": self.timestamp.isoformat(),
            "confianca_lpr": self.confianca_lpr,
            "andar": self.andar,
            "status": self.status.value,
            "valor_calculado": self.valor_calculado,
            "tempo_permanencia_minutos": self.tempo_permanencia_minutos,
            "erro_descricao": self.erro_descricao
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Evento':
        """Cria um evento a partir de um dicionário."""
        return cls(
            id=data.get("id"),
            placa=data["placa"],
            tipo=TipoEvento(data["tipo"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            confianca_lpr=data["confianca_lpr"],
            andar=data.get("andar", "terreo"),
            status=StatusEvento(data.get("status", "pendente")),
            valor_calculado=data.get("valor_calculado"),
            tempo_permanencia_minutos=data.get("tempo_permanencia_minutos"),
            erro_descricao=data.get("erro_descricao")
        )


class EventoResposta:
    """Resposta do servidor central para um evento."""
    
    def __init__(
        self,
        evento_id: str,
        sucesso: bool,
        acao: str,
        valor: Optional[float] = None,
        tempo_permanencia: Optional[int] = None,
        mensagem: Optional[str] = None
    ):
        self.evento_id = evento_id
        self.sucesso = sucesso
        self.acao = acao
        self.valor = valor
        self.tempo_permanencia = tempo_permanencia
        self.mensagem = mensagem
    
    def dict(self) -> dict:
        """Converte a resposta para dicionário."""
        return {
            "evento_id": self.evento_id,
            "sucesso": self.sucesso,
            "acao": self.acao,
            "valor": self.valor,
            "tempo_permanencia": self.tempo_permanencia,
            "mensagem": self.mensagem
        }
