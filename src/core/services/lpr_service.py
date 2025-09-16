"""
Serviço de reconhecimento de placas (LPR).
"""
import asyncio
import random
import string
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class LPRService:
    """Serviço para reconhecimento de placas."""
    
    def __init__(self, modo_simulacao: bool = True, timeout: int = 5):
        self.modo_simulacao = modo_simulacao
        self.timeout = timeout
        self.placas_simuladas = [
            "ABC1234", "DEF5678", "GHI9012", "JKL3456",
            "MNO7890", "PQR1234", "STU5678", "VWX9012",
            "YZA3456", "BCD7890"
        ]
    
    async def capturar_placa(self) -> Tuple[Optional[str], float]:
        """
        Captura uma placa usando LPR.
        
        Returns:
            Tuple[placa, confiança]: A placa capturada e o nível de confiança (0-1)
        """
        if self.modo_simulacao:
            return await self._simular_captura()
        else:
            return await self._capturar_hardware()
    
    async def _simular_captura(self) -> Tuple[Optional[str], float]:
        """Simula a captura de uma placa."""
        logger.info("Iniciando simulação de captura de placa...")
        
        # Simula delay de processamento
        await asyncio.sleep(random.uniform(1, 3))
        
        # 90% de chance de sucesso
        if random.random() < 0.9:
            placa = random.choice(self.placas_simuladas)
            confianca = random.uniform(0.7, 0.98)
            logger.info(f"Placa capturada: {placa} (confiança: {confianca:.2f})")
            return placa, confianca
        else:
            logger.warning("Falha na captura da placa")
            return None, 0.0
    
    async def _capturar_hardware(self) -> Tuple[Optional[str], float]:
        """Captura placa usando hardware real."""
        logger.info("Iniciando captura via hardware...")
        
        try:
            # Aqui seria implementada a comunicação com a câmera LPR real
            # Via MODBUS ou protocolo específico do fabricante
            
            # Por enquanto, retorna simulação
            await asyncio.sleep(2)
            
            # Simulando resposta do hardware
            placa = self._gerar_placa_aleatoria()
            confianca = random.uniform(0.8, 0.95)
            
            logger.info(f"Placa capturada via hardware: {placa} (confiança: {confianca:.2f})")
            return placa, confianca
            
        except Exception as e:
            logger.error(f"Erro na captura via hardware: {e}")
            return None, 0.0
    
    def _gerar_placa_aleatoria(self) -> str:
        """Gera uma placa aleatória no formato brasileiro."""
        letras = ''.join(random.choices(string.ascii_uppercase, k=3))
        numeros = ''.join(random.choices(string.digits, k=4))
        return f"{letras}{numeros}"
    
    async def validar_placa(self, placa: str, confianca_minima: float = 0.7) -> bool:
        """
        Valida se uma placa capturada atende aos critérios mínimos.
        
        Args:
            placa: A placa capturada
            confianca_minima: Nível mínimo de confiança aceito
            
        Returns:
            bool: True se a placa é válida
        """
        if not placa:
            return False
        
        # Validação básica do formato da placa
        if len(placa) != 7:
            logger.warning(f"Placa com formato inválido: {placa}")
            return False
        
        # Verifica se os primeiros 3 caracteres são letras
        if not placa[:3].isalpha():
            logger.warning(f"Formato de placa inválido: {placa}")
            return False
        
        # Verifica se os últimos 4 caracteres são números
        if not placa[3:].isdigit():
            logger.warning(f"Formato de placa inválido: {placa}")
            return False
        
        logger.info(f"Placa validada com sucesso: {placa}")
        return True
    
    def configurar_modo(self, modo_simulacao: bool):
        """Configura o modo de operação (simulação ou hardware)."""
        self.modo_simulacao = modo_simulacao
        modo_str = "simulação" if modo_simulacao else "hardware"
        logger.info(f"Modo LPR configurado para: {modo_str}")
    
    def obter_estatisticas(self) -> dict:
        """Retorna estatísticas do serviço LPR."""
        return {
            "modo": "simulação" if self.modo_simulacao else "hardware",
            "timeout": self.timeout,
            "total_placas_simuladas": len(self.placas_simuladas)
        }
