"""
Serviço de controle de cancelas.
"""
import asyncio
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class StatusCancela(Enum):
    FECHADA = "fechada"
    ABRINDO = "abrindo"
    ABERTA = "aberta"
    FECHANDO = "fechando"
    ERRO = "erro"


class TipoCancela(Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class CancelaService:
    """Serviço para controle de cancelas."""
    
    def __init__(self, tipo: TipoCancela, endereco_modbus: int, modo_simulacao: bool = True):
        self.tipo = tipo
        self.endereco_modbus = endereco_modbus
        self.modo_simulacao = modo_simulacao
        self.status = StatusCancela.FECHADA
        self.sensor_presenca = False
        self.sensor_passagem = False
        self.timeout_abertura = 10  # segundos
        
    async def detectar_presenca(self) -> bool:
        """
        Detecta presença de veículo no sensor.
        
        Returns:
            bool: True se há veículo presente
        """
        if self.modo_simulacao:
            return await self._simular_sensor_presenca()
        else:
            return await self._ler_sensor_hardware()
    
    async def _simular_sensor_presenca(self) -> bool:
        """Simula detecção de presença."""
        # Em modo simulação, alterna a presença periodicamente
        import random
        self.sensor_presenca = random.random() < 0.3  # 30% chance de detectar veículo
        
        if self.sensor_presenca:
            logger.info(f"Sensor {self.tipo.value}: Veículo detectado")
        
        return self.sensor_presenca
    
    async def _ler_sensor_hardware(self) -> bool:
        """Lê sensor via MODBUS."""
        try:
            # Aqui seria implementada a leitura via MODBUS
            # Por enquanto, simula
            await asyncio.sleep(0.1)
            self.sensor_presenca = False
            return self.sensor_presenca
            
        except Exception as e:
            logger.error(f"Erro ao ler sensor {self.tipo.value}: {e}")
            return False
    
    async def abrir_cancela(self) -> bool:
        """
        Abre a cancela.
        
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        if self.status == StatusCancela.ABERTA:
            logger.warning(f"Cancela {self.tipo.value} já está aberta")
            return True
        
        logger.info(f"Abrindo cancela {self.tipo.value}...")
        self.status = StatusCancela.ABRINDO
        
        try:
            if self.modo_simulacao:
                await self._simular_abertura()
            else:
                await self._abrir_via_modbus()
            
            self.status = StatusCancela.ABERTA
            logger.info(f"Cancela {self.tipo.value} aberta com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao abrir cancela {self.tipo.value}: {e}")
            self.status = StatusCancela.ERRO
            return False
    
    async def _simular_abertura(self):
        """Simula abertura da cancela."""
        await asyncio.sleep(2)  # Simula tempo de abertura
    
    async def _abrir_via_modbus(self):
        """Abre cancela via MODBUS."""
        # Aqui seria implementado o comando MODBUS
        await asyncio.sleep(2)
    
    async def fechar_cancela(self) -> bool:
        """
        Fecha a cancela.
        
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        if self.status == StatusCancela.FECHADA:
            logger.warning(f"Cancela {self.tipo.value} já está fechada")
            return True
        
        logger.info(f"Fechando cancela {self.tipo.value}...")
        self.status = StatusCancela.FECHANDO
        
        try:
            if self.modo_simulacao:
                await self._simular_fechamento()
            else:
                await self._fechar_via_modbus()
            
            self.status = StatusCancela.FECHADA
            logger.info(f"Cancela {self.tipo.value} fechada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao fechar cancela {self.tipo.value}: {e}")
            self.status = StatusCancela.ERRO
            return False
    
    async def _simular_fechamento(self):
        """Simula fechamento da cancela."""
        await asyncio.sleep(2)  # Simula tempo de fechamento
    
    async def _fechar_via_modbus(self):
        """Fecha cancela via MODBUS."""
        # Aqui seria implementado o comando MODBUS
        await asyncio.sleep(2)
    
    async def aguardar_passagem(self, timeout: Optional[int] = None) -> bool:
        """
        Aguarda o veículo passar pela cancela.
        
        Args:
            timeout: Tempo limite em segundos
            
        Returns:
            bool: True se o veículo passou
        """
        timeout = timeout or self.timeout_abertura
        logger.info(f"Aguardando passagem do veículo (timeout: {timeout}s)...")
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if self.modo_simulacao:
                # Em simulação, simula passagem após alguns segundos
                await asyncio.sleep(1)
                if (asyncio.get_event_loop().time() - start_time) > 3:
                    logger.info("Veículo passou pela cancela (simulação)")
                    return True
            else:
                # Aqui seria implementada a leitura do sensor de passagem
                await asyncio.sleep(0.5)
                # Por enquanto, simula
                if (asyncio.get_event_loop().time() - start_time) > 5:
                    return True
        
        logger.warning("Timeout na passagem do veículo")
        return False
    
    async def ciclo_completo(self) -> bool:
        """
        Executa um ciclo completo: abrir -> aguardar passagem -> fechar.
        
        Returns:
            bool: True se o ciclo foi bem-sucedido
        """
        logger.info(f"Iniciando ciclo completo da cancela {self.tipo.value}")
        
        # Abre a cancela
        if not await self.abrir_cancela():
            return False
        
        # Aguarda passagem
        if not await self.aguardar_passagem():
            logger.warning("Veículo não passou - fechando cancela")
            await self.fechar_cancela()
            return False
        
        # Fecha a cancela
        if not await self.fechar_cancela():
            return False
        
        logger.info(f"Ciclo completo da cancela {self.tipo.value} finalizado")
        return True
    
    def obter_status(self) -> dict:
        """Retorna o status atual da cancela."""
        return {
            "tipo": self.tipo.value,
            "status": self.status.value,
            "endereco_modbus": self.endereco_modbus,
            "sensor_presenca": self.sensor_presenca,
            "sensor_passagem": self.sensor_passagem,
            "modo_simulacao": self.modo_simulacao
        }
    
    def configurar_modo(self, modo_simulacao: bool):
        """Configura o modo de operação."""
        self.modo_simulacao = modo_simulacao
        modo_str = "simulação" if modo_simulacao else "hardware"
        logger.info(f"Modo cancela {self.tipo.value} configurado para: {modo_str}")
