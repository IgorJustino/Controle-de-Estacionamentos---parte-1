"""
Servidor Distribuído do Térreo - Controla cancelas, sensores e comunicação com o Central.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Optional
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.models.evento import Evento, TipoEvento
from src.core.services.lpr_service import LPRService
from src.core.services.cancela_service import CancelaService, TipoCancela
from src.core.services.placar_service import PlacarService
from src.clients.modbus_client import ModbusClient

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/servidor_terreo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EstadoCancela(Enum):
    AGUARDANDO = "aguardando"
    DETECTOU_VEICULO = "detectou_veiculo"
    CAPTURANDO_PLACA = "capturando_placa"
    ENVIANDO_CENTRAL = "enviando_central"
    AGUARDANDO_RESPOSTA = "aguardando_resposta"
    ABRINDO_CANCELA = "abrindo_cancela"
    AGUARDANDO_PASSAGEM = "aguardando_passagem"
    FECHANDO_CANCELA = "fechando_cancela"
    ERRO = "erro"


class ServidorTerreo:
    """Servidor distribuído do térreo."""
    
    def __init__(self):
        # Configurações
        self.central_host = os.getenv("CENTRAL_HOST", "localhost")
        self.central_port = int(os.getenv("CENTRAL_PORT", "8080"))
        self.modo_simulacao = os.getenv("MODE", "simulation") == "simulation"
        
        # Endereços MODBUS
        self.endereco_entrada = int(os.getenv("MODBUS_ADDRESS_ENTRADA", "1"))
        self.endereco_saida = int(os.getenv("MODBUS_ADDRESS_SAIDA", "2"))
        self.endereco_placar = int(os.getenv("MODBUS_ADDRESS_PLACAR", "3"))
        
        # Configurações LPR
        self.lpr_timeout = int(os.getenv("LPR_TIMEOUT", "5"))
        self.lpr_confidence_min = float(os.getenv("LPR_CONFIDENCE_MIN", "0.8"))
        
        # Cliente MODBUS
        self.modbus_client = ModbusClient(
            port=os.getenv("SERIAL_PORT", "/dev/ttyUSB0"),
            baudrate=int(os.getenv("MODBUS_BAUDRATE", "9600")),
            modo_simulacao=self.modo_simulacao
        )
        
        # Serviços
        self.lpr_service = LPRService(
            modo_simulacao=self.modo_simulacao,
            timeout=self.lpr_timeout
        )
        
        self.cancela_entrada = CancelaService(
            tipo=TipoCancela.ENTRADA,
            endereco_modbus=self.endereco_entrada,
            modo_simulacao=self.modo_simulacao
        )
        
        self.cancela_saida = CancelaService(
            tipo=TipoCancela.SAIDA,
            endereco_modbus=self.endereco_saida,
            modo_simulacao=self.modo_simulacao
        )
        
        self.placar_service = PlacarService(
            endereco_modbus=self.endereco_placar,
            total_vagas=int(os.getenv("TOTAL_VAGAS", "8")),
            endereco_inicial_vagas=int(os.getenv("ENDERECO_INICIAL_VAGAS", "0")),
            modo_simulacao=self.modo_simulacao
        )
        
        # Estados das máquinas
        self.estado_entrada = EstadoCancela.AGUARDANDO
        self.estado_saida = EstadoCancela.AGUARDANDO
        
        # Tarefas em execução
        self.tarefas = []
    
    async def iniciar(self):
        """Inicia o servidor do térreo."""
        logger.info("Iniciando Servidor do Térreo...")
        
        # Conecta MODBUS
        if not await self.modbus_client.conectar():
            logger.error("Falha ao conectar MODBUS - usando modo simulação")
            self.modo_simulacao = True
            self.modbus_client.modo_simulacao = True
        
        # Inicia tarefas
        self.tarefas = [
            asyncio.create_task(self._maquina_estado_entrada()),
            asyncio.create_task(self._maquina_estado_saida()),
            asyncio.create_task(self._monitorar_vagas()),
            asyncio.create_task(self._tarefa_manutencao())
        ]
        
        logger.info("Servidor do Térreo iniciado")
        
        try:
            # Aguarda todas as tarefas
            await asyncio.gather(*self.tarefas)
        except KeyboardInterrupt:
            logger.info("Servidor interrompido pelo usuário")
        finally:
            await self._parar()
    
    async def _maquina_estado_entrada(self):
        """Máquina de estados para cancela de entrada."""
        logger.info("Iniciando máquina de estados da entrada")
        
        while True:
            try:
                if self.estado_entrada == EstadoCancela.AGUARDANDO:
                    await self._aguardar_veiculo_entrada()
                
                elif self.estado_entrada == EstadoCancela.DETECTOU_VEICULO:
                    await self._processar_entrada()
                
                elif self.estado_entrada == EstadoCancela.ERRO:
                    await self._recuperar_erro_entrada()
                
                await asyncio.sleep(1)  # Evita loop muito rápido
                
            except Exception as e:
                logger.error(f"Erro na máquina de entrada: {e}")
                self.estado_entrada = EstadoCancela.ERRO
                await asyncio.sleep(5)
    
    async def _maquina_estado_saida(self):
        """Máquina de estados para cancela de saída."""
        logger.info("Iniciando máquina de estados da saída")
        
        while True:
            try:
                if self.estado_saida == EstadoCancela.AGUARDANDO:
                    await self._aguardar_veiculo_saida()
                
                elif self.estado_saida == EstadoCancela.DETECTOU_VEICULO:
                    await self._processar_saida()
                
                elif self.estado_saida == EstadoCancela.ERRO:
                    await self._recuperar_erro_saida()
                
                await asyncio.sleep(1)  # Evita loop muito rápido
                
            except Exception as e:
                logger.error(f"Erro na máquina de saída: {e}")
                self.estado_saida = EstadoCancela.ERRO
                await asyncio.sleep(5)
    
    async def _aguardar_veiculo_entrada(self):
        """Aguarda veículo na entrada."""
        if await self.cancela_entrada.detectar_presenca():
            logger.info("Veículo detectado na entrada")
            self.estado_entrada = EstadoCancela.DETECTOU_VEICULO
    
    async def _aguardar_veiculo_saida(self):
        """Aguarda veículo na saída."""
        if await self.cancela_saida.detectar_presenca():
            logger.info("Veículo detectado na saída")
            self.estado_saida = EstadoCancela.DETECTOU_VEICULO
    
    async def _processar_entrada(self):
        """Processa entrada de veículo."""
        try:
            logger.info("Processando entrada de veículo")
            
            # Captura placa
            self.estado_entrada = EstadoCancela.CAPTURANDO_PLACA
            placa, confianca = await self.lpr_service.capturar_placa()
            
            if not placa or confianca < self.lpr_confidence_min:
                logger.warning("Falha na captura da placa na entrada")
                self.estado_entrada = EstadoCancela.ERRO
                return
            
            # Valida placa
            if not await self.lpr_service.validar_placa(placa):
                logger.warning(f"Placa inválida na entrada: {placa}")
                self.estado_entrada = EstadoCancela.ERRO
                return
            
            # Cria evento
            evento = Evento(
                placa=placa,
                tipo=TipoEvento.ENTRADA,
                timestamp=datetime.now(),
                confianca_lpr=confianca,
                andar="terreo"
            )
            
            # Envia ao central
            self.estado_entrada = EstadoCancela.ENVIANDO_CENTRAL
            resposta = await self._enviar_evento_central(evento)
            
            if resposta and resposta.get("sucesso"):
                if resposta.get("acao") == "abrir_cancela":
                    # Abre cancela
                    self.estado_entrada = EstadoCancela.ABRINDO_CANCELA
                    if await self.cancela_entrada.ciclo_completo():
                        logger.info(f"Entrada processada com sucesso: {placa}")
                        
                        # Marca uma vaga como ocupada
                        vaga_livre = self.placar_service.encontrar_vaga_livre()
                        if vaga_livre != -1:
                            self.placar_service.ocupar_vaga(vaga_livre)
                    else:
                        logger.error("Falha no ciclo da cancela de entrada")
                        self.estado_entrada = EstadoCancela.ERRO
                        return
                else:
                    logger.warning(f"Entrada negada para {placa}: {resposta.get('mensagem')}")
            else:
                logger.error("Resposta inválida do servidor central")
                self.estado_entrada = EstadoCancela.ERRO
                return
            
            # Volta ao estado inicial
            self.estado_entrada = EstadoCancela.AGUARDANDO
            
        except Exception as e:
            logger.error(f"Erro ao processar entrada: {e}")
            self.estado_entrada = EstadoCancela.ERRO
    
    async def _processar_saida(self):
        """Processa saída de veículo."""
        try:
            logger.info("Processando saída de veículo")
            
            # Captura placa
            self.estado_saida = EstadoCancela.CAPTURANDO_PLACA
            placa, confianca = await self.lpr_service.capturar_placa()
            
            if not placa or confianca < self.lpr_confidence_min:
                logger.warning("Falha na captura da placa na saída")
                self.estado_saida = EstadoCancela.ERRO
                return
            
            # Valida placa
            if not await self.lpr_service.validar_placa(placa):
                logger.warning(f"Placa inválida na saída: {placa}")
                self.estado_saida = EstadoCancela.ERRO
                return
            
            # Cria evento
            evento = Evento(
                placa=placa,
                tipo=TipoEvento.SAIDA,
                timestamp=datetime.now(),
                confianca_lpr=confianca,
                andar="terreo"
            )
            
            # Envia ao central
            self.estado_saida = EstadoCancela.ENVIANDO_CENTRAL
            resposta = await self._enviar_evento_central(evento)
            
            if resposta and resposta.get("sucesso"):
                acao = resposta.get("acao")
                if acao == "cobrar_valor":
                    valor = resposta.get("valor", 0)
                    tempo = resposta.get("tempo_permanencia", 0)
                    
                    logger.info(f"Cobrança para {placa}: R$ {valor:.2f} ({tempo} min)")
                    
                    # Abre cancela
                    self.estado_saida = EstadoCancela.ABRINDO_CANCELA
                    if await self.cancela_saida.ciclo_completo():
                        logger.info(f"Saída processada com sucesso: {placa}")
                        
                        # Libera uma vaga (simplificação - seria baseada na vaga específica)
                        for vaga in range(self.placar_service.total_vagas):
                            if self.placar_service.vagas[vaga]:
                                self.placar_service.liberar_vaga(vaga)
                                break
                    else:
                        logger.error("Falha no ciclo da cancela de saída")
                        self.estado_saida = EstadoCancela.ERRO
                        return
                else:
                    logger.warning(f"Saída negada para {placa}: {resposta.get('mensagem')}")
            else:
                logger.error("Resposta inválida do servidor central para saída")
                self.estado_saida = EstadoCancela.ERRO
                return
            
            # Volta ao estado inicial
            self.estado_saida = EstadoCancela.AGUARDANDO
            
        except Exception as e:
            logger.error(f"Erro ao processar saída: {e}")
            self.estado_saida = EstadoCancela.ERRO
    
    async def _enviar_evento_central(self, evento: Evento) -> Optional[dict]:
        """Envia evento ao servidor central."""
        try:
            # Conecta ao servidor central
            reader, writer = await asyncio.open_connection(
                self.central_host,
                self.central_port
            )
            
            # Envia evento
            dados = evento.to_dict()
            mensagem = json.dumps(dados) + '\n'
            writer.write(mensagem.encode('utf-8'))
            await writer.drain()
            
            # Recebe resposta
            data = await reader.read(1024)
            resposta_str = data.decode('utf-8').strip()
            
            # Fecha conexão
            writer.close()
            await writer.wait_closed()
            
            # Decodifica resposta
            resposta = json.loads(resposta_str)
            logger.debug(f"Resposta do central: {resposta}")
            
            return resposta
            
        except Exception as e:
            logger.error(f"Erro ao comunicar com servidor central: {e}")
            return None
    
    async def _monitorar_vagas(self):
        """Monitora estado das vagas."""
        logger.info("Iniciando monitoramento de vagas")
        
        while True:
            try:
                await self.placar_service.atualizar_vagas()
                await asyncio.sleep(5)  # Verifica a cada 5 segundos
            except Exception as e:
                logger.error(f"Erro no monitoramento de vagas: {e}")
                await asyncio.sleep(10)
    
    async def _tarefa_manutencao(self):
        """Tarefa de manutenção e limpeza."""
        logger.info("Iniciando tarefa de manutenção")
        
        while True:
            try:
                # Log de estatísticas a cada 5 minutos
                await asyncio.sleep(300)
                
                stats = self.obter_estatisticas()
                logger.info(f"Estatísticas: {stats}")
                
            except Exception as e:
                logger.error(f"Erro na tarefa de manutenção: {e}")
                await asyncio.sleep(60)
    
    async def _recuperar_erro_entrada(self):
        """Tenta recuperar de erros na entrada."""
        logger.info("Tentando recuperar erro na entrada...")
        await asyncio.sleep(10)  # Aguarda antes de tentar novamente
        self.estado_entrada = EstadoCancela.AGUARDANDO
    
    async def _recuperar_erro_saida(self):
        """Tenta recuperar de erros na saída."""
        logger.info("Tentando recuperar erro na saída...")
        await asyncio.sleep(10)  # Aguarda antes de tentar novamente
        self.estado_saida = EstadoCancela.AGUARDANDO
    
    async def _parar(self):
        """Para o servidor e limpa recursos."""
        logger.info("Parando servidor do térreo...")
        
        # Cancela tarefas
        for tarefa in self.tarefas:
            tarefa.cancel()
        
        # Desconecta MODBUS
        await self.modbus_client.desconectar()
        
        logger.info("Servidor do térreo parado")
    
    def obter_estatisticas(self) -> dict:
        """Retorna estatísticas do servidor."""
        return {
            "estado_entrada": self.estado_entrada.value,
            "estado_saida": self.estado_saida.value,
            "modo_simulacao": self.modo_simulacao,
            "modbus_conectado": self.modbus_client.conectado,
            "cancela_entrada": self.cancela_entrada.obter_status(),
            "cancela_saida": self.cancela_saida.obter_status(),
            "placar": self.placar_service.obter_estatisticas()
        }


async def main():
    """Função principal."""
    servidor = ServidorTerreo()
    
    try:
        await servidor.iniciar()
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro no servidor: {e}")


if __name__ == "__main__":
    asyncio.run(main())
