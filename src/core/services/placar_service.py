"""
Serviço de controle do placar de vagas.
"""
import asyncio
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class PlacarService:
    """Serviço para controle do placar de vagas."""
    
    def __init__(
        self,
        endereco_modbus: int,
        total_vagas: int = 8,
        endereco_inicial_vagas: int = 0,
        modo_simulacao: bool = True
    ):
        self.endereco_modbus = endereco_modbus
        self.total_vagas = total_vagas
        self.endereco_inicial_vagas = endereco_inicial_vagas
        self.modo_simulacao = modo_simulacao
        
        # Estado das vagas (True = ocupada, False = livre)
        self.vagas: Dict[int, bool] = {i: False for i in range(total_vagas)}
        self.vagas_livres = total_vagas
        
    async def ler_sensores_vagas(self) -> Dict[int, bool]:
        """
        Lê o estado de todos os sensores de vagas.
        
        Returns:
            Dict[int, bool]: Estado de cada vaga (True = ocupada)
        """
        if self.modo_simulacao:
            return await self._simular_leitura_vagas()
        else:
            return await self._ler_vagas_modbus()
    
    async def _simular_leitura_vagas(self) -> Dict[int, bool]:
        """Simula a leitura das vagas."""
        import random
        
        # Simula mudanças ocasionais nas vagas
        for vaga in range(self.total_vagas):
            if random.random() < 0.05:  # 5% chance de mudança
                self.vagas[vaga] = not self.vagas[vaga]
        
        return self.vagas.copy()
    
    async def _ler_vagas_modbus(self) -> Dict[int, bool]:
        """Lê as vagas via MODBUS."""
        try:
            # Aqui seria implementada a leitura via MODBUS
            # dos endereços dos sensores das vagas
            await asyncio.sleep(0.1)
            
            # Por enquanto, retorna estado atual
            return self.vagas.copy()
            
        except Exception as e:
            logger.error(f"Erro ao ler sensores de vagas: {e}")
            return self.vagas.copy()
    
    async def atualizar_vagas(self) -> bool:
        """
        Atualiza o estado das vagas lendo os sensores.
        
        Returns:
            bool: True se houve mudanças
        """
        estado_anterior = self.vagas.copy()
        vagas_livres_anterior = self.vagas_livres
        
        # Lê estado atual dos sensores
        novo_estado = await self.ler_sensores_vagas()
        self.vagas = novo_estado
        
        # Calcula vagas livres
        self.vagas_livres = sum(1 for ocupada in self.vagas.values() if not ocupada)
        
        # Verifica se houve mudanças
        mudancas = estado_anterior != self.vagas
        
        if mudancas:
            logger.info(f"Vagas atualizadas: {self.vagas_livres}/{self.total_vagas} livres")
            await self._atualizar_placar()
        
        return mudancas
    
    async def _atualizar_placar(self) -> bool:
        """Atualiza o display do placar."""
        try:
            if self.modo_simulacao:
                await self._simular_atualizacao_placar()
            else:
                await self._atualizar_placar_modbus()
            
            logger.info(f"Placar atualizado: {self.vagas_livres} vagas livres")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar placar: {e}")
            return False
    
    async def _simular_atualizacao_placar(self):
        """Simula atualização do placar."""
        await asyncio.sleep(0.5)
        logger.debug(f"[PLACAR] Vagas livres: {self.vagas_livres:02d}")
    
    async def _atualizar_placar_modbus(self):
        """Atualiza placar via MODBUS."""
        # Aqui seria implementada a escrita via MODBUS
        # para atualizar o display do placar
        await asyncio.sleep(0.5)
    
    def ocupar_vaga(self, numero_vaga: int) -> bool:
        """
        Marca uma vaga como ocupada.
        
        Args:
            numero_vaga: Número da vaga (0-based)
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        if numero_vaga < 0 or numero_vaga >= self.total_vagas:
            logger.error(f"Número de vaga inválido: {numero_vaga}")
            return False
        
        if self.vagas[numero_vaga]:
            logger.warning(f"Vaga {numero_vaga} já está ocupada")
            return False
        
        self.vagas[numero_vaga] = True
        self.vagas_livres -= 1
        logger.info(f"Vaga {numero_vaga} marcada como ocupada")
        
        # Agenda atualização do placar
        asyncio.create_task(self._atualizar_placar())
        return True
    
    def liberar_vaga(self, numero_vaga: int) -> bool:
        """
        Marca uma vaga como livre.
        
        Args:
            numero_vaga: Número da vaga (0-based)
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        if numero_vaga < 0 or numero_vaga >= self.total_vagas:
            logger.error(f"Número de vaga inválido: {numero_vaga}")
            return False
        
        if not self.vagas[numero_vaga]:
            logger.warning(f"Vaga {numero_vaga} já está livre")
            return False
        
        self.vagas[numero_vaga] = False
        self.vagas_livres += 1
        logger.info(f"Vaga {numero_vaga} marcada como livre")
        
        # Agenda atualização do placar
        asyncio.create_task(self._atualizar_placar())
        return True
    
    def encontrar_vaga_livre(self) -> int:
        """
        Encontra uma vaga livre.
        
        Returns:
            int: Número da vaga livre (-1 se não houver)
        """
        for numero, ocupada in self.vagas.items():
            if not ocupada:
                return numero
        return -1
    
    def obter_estatisticas(self) -> dict:
        """Retorna estatísticas das vagas."""
        ocupadas = [num for num, ocupada in self.vagas.items() if ocupada]
        livres = [num for num, ocupada in self.vagas.items() if not ocupada]
        
        return {
            "total_vagas": self.total_vagas,
            "vagas_livres": self.vagas_livres,
            "vagas_ocupadas": self.total_vagas - self.vagas_livres,
            "percentual_ocupacao": ((self.total_vagas - self.vagas_livres) / self.total_vagas) * 100,
            "vagas_ocupadas_numeros": ocupadas,
            "vagas_livres_numeros": livres,
            "estacionamento_cheio": self.vagas_livres == 0
        }
    
    def obter_status(self) -> dict:
        """Retorna o status atual do placar."""
        return {
            "endereco_modbus": self.endereco_modbus,
            "modo_simulacao": self.modo_simulacao,
            "vagas": self.vagas.copy(),
            **self.obter_estatisticas()
        }
    
    def configurar_modo(self, modo_simulacao: bool):
        """Configura o modo de operação."""
        self.modo_simulacao = modo_simulacao
        modo_str = "simulação" if modo_simulacao else "hardware"
        logger.info(f"Modo placar configurado para: {modo_str}")
    
    async def iniciar_monitoramento(self, intervalo: int = 5):
        """
        Inicia monitoramento contínuo das vagas.
        
        Args:
            intervalo: Intervalo entre verificações em segundos
        """
        logger.info(f"Iniciando monitoramento das vagas (intervalo: {intervalo}s)")
        
        while True:
            try:
                await self.atualizar_vagas()
                await asyncio.sleep(intervalo)
            except Exception as e:
                logger.error(f"Erro no monitoramento das vagas: {e}")
                await asyncio.sleep(intervalo)
