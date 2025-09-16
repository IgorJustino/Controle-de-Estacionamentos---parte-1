"""
Modelo de dados para veículos no estacionamento.
"""
from datetime import datetime
from enum import Enum
from typing import Optional


class StatusVeiculo(Enum):
    ESTACIONADO = "estacionado"
    SAIU = "saiu"
    BLOQUEADO = "bloqueado"


class Veiculo:
    """Representa um veículo no sistema de estacionamento."""
    
    def __init__(
        self,
        placa: str,
        timestamp_entrada: datetime,
        andar: str = "terreo",
        vaga: Optional[int] = None
    ):
        self.placa = placa
        self.timestamp_entrada = timestamp_entrada
        self.timestamp_saida: Optional[datetime] = None
        self.andar = andar
        self.vaga = vaga
        self.status = StatusVeiculo.ESTACIONADO
        self.valor_calculado: Optional[float] = None
        self.tempo_permanencia_minutos: Optional[int] = None
    
    def calcular_tempo_permanencia(self, timestamp_saida: datetime) -> int:
        """Calcula o tempo de permanência em minutos."""
        delta = timestamp_saida - self.timestamp_entrada
        minutos = int(delta.total_seconds() / 60)
        # Arredonda para cima se houver segundos excedentes
        if delta.total_seconds() % 60 > 0:
            minutos += 1
        return minutos
    
    def calcular_valor(self, preco_por_minuto: float, valor_minimo: float) -> float:
        """Calcula o valor a ser cobrado."""
        if self.tempo_permanencia_minutos is None:
            return valor_minimo
        
        valor = self.tempo_permanencia_minutos * preco_por_minuto
        return max(valor, valor_minimo)
    
    def processar_saida(
        self,
        timestamp_saida: datetime,
        preco_por_minuto: float,
        valor_minimo: float
    ) -> dict:
        """Processa a saída do veículo e calcula valores."""
        self.timestamp_saida = timestamp_saida
        self.tempo_permanencia_minutos = self.calcular_tempo_permanencia(timestamp_saida)
        self.valor_calculado = self.calcular_valor(preco_por_minuto, valor_minimo)
        self.status = StatusVeiculo.SAIU
        
        return {
            "placa": self.placa,
            "tempo_permanencia_minutos": self.tempo_permanencia_minutos,
            "valor_calculado": self.valor_calculado,
            "timestamp_entrada": self.timestamp_entrada.isoformat(),
            "timestamp_saida": self.timestamp_saida.isoformat()
        }
    
    def to_dict(self) -> dict:
        """Converte o veículo para dicionário."""
        return {
            "placa": self.placa,
            "timestamp_entrada": self.timestamp_entrada.isoformat(),
            "timestamp_saida": self.timestamp_saida.isoformat() if self.timestamp_saida else None,
            "andar": self.andar,
            "vaga": self.vaga,
            "status": self.status.value,
            "valor_calculado": self.valor_calculado,
            "tempo_permanencia_minutos": self.tempo_permanencia_minutos
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Veiculo':
        """Cria um veículo a partir de um dicionário."""
        veiculo = cls(
            placa=data["placa"],
            timestamp_entrada=datetime.fromisoformat(data["timestamp_entrada"]),
            andar=data.get("andar", "terreo"),
            vaga=data.get("vaga")
        )
        
        if data.get("timestamp_saida"):
            veiculo.timestamp_saida = datetime.fromisoformat(data["timestamp_saida"])
        
        veiculo.status = StatusVeiculo(data.get("status", "estacionado"))
        veiculo.valor_calculado = data.get("valor_calculado")
        veiculo.tempo_permanencia_minutos = data.get("tempo_permanencia_minutos")
        
        return veiculo
