"""
Cliente MODBUS para comunicação com hardware.
"""
import asyncio
import logging
from typing import Optional, Union, List
import os

logger = logging.getLogger(__name__)

# Importação condicional do pymodbus
try:
    from pymodbus.client import ModbusSerialClient, ModbusTcpClient
    from pymodbus.exceptions import ModbusException
    PYMODBUS_AVAILABLE = True
except ImportError:
    logger.warning("PyModbus não está disponível. Usando modo simulação.")
    PYMODBUS_AVAILABLE = False


class ModbusClient:
    """Cliente MODBUS para comunicação com dispositivos."""
    
    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        modo_simulacao: bool = True
    ):
        self.port = port
        self.baudrate = baudrate
        self.modo_simulacao = modo_simulacao or not PYMODBUS_AVAILABLE
        self.client: Optional[Union[ModbusSerialClient, ModbusTcpClient]] = None
        self.conectado = False
        
        if not self.modo_simulacao and not PYMODBUS_AVAILABLE:
            logger.warning("PyModbus não disponível. Forçando modo simulação.")
            self.modo_simulacao = True
    
    async def conectar(self) -> bool:
        """
        Conecta ao dispositivo MODBUS.
        
        Returns:
            bool: True se conectado com sucesso
        """
        if self.modo_simulacao:
            logger.info("Conectando em modo simulação")
            self.conectado = True
            return True
        
        try:
            # Verifica se a porta serial existe
            if not os.path.exists(self.port):
                logger.error(f"Porta serial não encontrada: {self.port}")
                return False
            
            # Cria cliente serial
            self.client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                timeout=3
            )
            
            # Conecta
            result = self.client.connect()
            self.conectado = result
            
            if self.conectado:
                logger.info(f"Conectado via MODBUS: {self.port} @ {self.baudrate}")
            else:
                logger.error("Falha na conexão MODBUS")
            
            return self.conectado
            
        except Exception as e:
            logger.error(f"Erro ao conectar MODBUS: {e}")
            self.conectado = False
            return False
    
    async def desconectar(self):
        """Desconecta do dispositivo MODBUS."""
        if self.modo_simulacao:
            logger.info("Desconectando modo simulação")
            self.conectado = False
            return
        
        if self.client and self.conectado:
            self.client.close()
            self.conectado = False
            logger.info("Desconectado do MODBUS")
    
    async def ler_coil(self, endereco: int, slave_id: int = 1) -> Optional[bool]:
        """
        Lê uma coil (entrada digital).
        
        Args:
            endereco: Endereço da coil
            slave_id: ID do dispositivo slave
            
        Returns:
            bool: Estado da coil (None se erro)
        """
        if self.modo_simulacao:
            return await self._simular_leitura_coil(endereco)
        
        if not self.conectado:
            logger.error("Cliente MODBUS não conectado")
            return None
        
        try:
            result = self.client.read_coils(endereco, 1, slave_id)
            
            if result.isError():
                logger.error(f"Erro ao ler coil {endereco}: {result}")
                return None
            
            valor = result.bits[0]
            logger.debug(f"Coil {endereco}: {valor}")
            return valor
            
        except Exception as e:
            logger.error(f"Erro ao ler coil {endereco}: {e}")
            return None
    
    async def escrever_coil(self, endereco: int, valor: bool, slave_id: int = 1) -> bool:
        """
        Escreve uma coil (saída digital).
        
        Args:
            endereco: Endereço da coil
            valor: Valor a escrever
            slave_id: ID do dispositivo slave
            
        Returns:
            bool: True se sucesso
        """
        if self.modo_simulacao:
            return await self._simular_escrita_coil(endereco, valor)
        
        if not self.conectado:
            logger.error("Cliente MODBUS não conectado")
            return False
        
        try:
            result = self.client.write_coil(endereco, valor, slave_id)
            
            if result.isError():
                logger.error(f"Erro ao escrever coil {endereco}: {result}")
                return False
            
            logger.debug(f"Coil {endereco} = {valor}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao escrever coil {endereco}: {e}")
            return False
    
    async def ler_holding_register(self, endereco: int, slave_id: int = 1) -> Optional[int]:
        """
        Lê um holding register.
        
        Args:
            endereco: Endereço do register
            slave_id: ID do dispositivo slave
            
        Returns:
            int: Valor do register (None se erro)
        """
        if self.modo_simulacao:
            return await self._simular_leitura_register(endereco)
        
        if not self.conectado:
            logger.error("Cliente MODBUS não conectado")
            return None
        
        try:
            result = self.client.read_holding_registers(endereco, 1, slave_id)
            
            if result.isError():
                logger.error(f"Erro ao ler register {endereco}: {result}")
                return None
            
            valor = result.registers[0]
            logger.debug(f"Register {endereco}: {valor}")
            return valor
            
        except Exception as e:
            logger.error(f"Erro ao ler register {endereco}: {e}")
            return None
    
    async def escrever_holding_register(
        self,
        endereco: int,
        valor: int,
        slave_id: int = 1
    ) -> bool:
        """
        Escreve um holding register.
        
        Args:
            endereco: Endereço do register
            valor: Valor a escrever
            slave_id: ID do dispositivo slave
            
        Returns:
            bool: True se sucesso
        """
        if self.modo_simulacao:
            return await self._simular_escrita_register(endereco, valor)
        
        if not self.conectado:
            logger.error("Cliente MODBUS não conectado")
            return False
        
        try:
            result = self.client.write_register(endereco, valor, slave_id)
            
            if result.isError():
                logger.error(f"Erro ao escrever register {endereco}: {result}")
                return False
            
            logger.debug(f"Register {endereco} = {valor}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao escrever register {endereco}: {e}")
            return False
    
    async def ler_multiplas_coils(
        self,
        endereco_inicial: int,
        quantidade: int,
        slave_id: int = 1
    ) -> Optional[List[bool]]:
        """
        Lê múltiplas coils.
        
        Args:
            endereco_inicial: Primeiro endereço
            quantidade: Número de coils a ler
            slave_id: ID do dispositivo slave
            
        Returns:
            List[bool]: Lista com valores das coils
        """
        if self.modo_simulacao:
            return await self._simular_leitura_multiplas_coils(endereco_inicial, quantidade)
        
        if not self.conectado:
            logger.error("Cliente MODBUS não conectado")
            return None
        
        try:
            result = self.client.read_coils(endereco_inicial, quantidade, slave_id)
            
            if result.isError():
                logger.error(f"Erro ao ler coils {endereco_inicial}-{endereco_inicial+quantidade-1}: {result}")
                return None
            
            valores = result.bits[:quantidade]
            logger.debug(f"Coils {endereco_inicial}-{endereco_inicial+quantidade-1}: {valores}")
            return valores
            
        except Exception as e:
            logger.error(f"Erro ao ler múltiplas coils: {e}")
            return None
    
    # Métodos de simulação
    async def _simular_leitura_coil(self, endereco: int) -> bool:
        """Simula leitura de coil."""
        import random
        await asyncio.sleep(0.1)
        valor = random.choice([True, False])
        logger.debug(f"[SIM] Coil {endereco}: {valor}")
        return valor
    
    async def _simular_escrita_coil(self, endereco: int, valor: bool) -> bool:
        """Simula escrita de coil."""
        await asyncio.sleep(0.1)
        logger.debug(f"[SIM] Escrevendo coil {endereco} = {valor}")
        return True
    
    async def _simular_leitura_register(self, endereco: int) -> int:
        """Simula leitura de register."""
        import random
        await asyncio.sleep(0.1)
        valor = random.randint(0, 100)
        logger.debug(f"[SIM] Register {endereco}: {valor}")
        return valor
    
    async def _simular_escrita_register(self, endereco: int, valor: int) -> bool:
        """Simula escrita de register."""
        await asyncio.sleep(0.1)
        logger.debug(f"[SIM] Escrevendo register {endereco} = {valor}")
        return True
    
    async def _simular_leitura_multiplas_coils(
        self,
        endereco_inicial: int,
        quantidade: int
    ) -> List[bool]:
        """Simula leitura de múltiplas coils."""
        import random
        await asyncio.sleep(0.1)
        valores = [random.choice([True, False]) for _ in range(quantidade)]
        logger.debug(f"[SIM] Coils {endereco_inicial}-{endereco_inicial+quantidade-1}: {valores}")
        return valores
    
    def obter_status(self) -> dict:
        """Retorna o status da conexão."""
        return {
            "conectado": self.conectado,
            "modo_simulacao": self.modo_simulacao,
            "port": self.port,
            "baudrate": self.baudrate,
            "pymodbus_disponivel": PYMODBUS_AVAILABLE
        }
