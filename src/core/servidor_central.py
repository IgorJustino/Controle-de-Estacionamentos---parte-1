"""
Servidor Central - Gerencia eventos e cálculos do estacionamento.
"""
import asyncio
import json
import logging
import sqlite3
import os
import sys
from datetime import datetime
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.models.evento import Evento, TipoEvento, StatusEvento, EventoResposta
from src.core.models.veiculo import Veiculo

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/servidor_central.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ServidorCentral:
    """Servidor Central do sistema de estacionamento."""
    
    def __init__(self):
        self.host = os.getenv("CENTRAL_HOST", "localhost")
        self.port = int(os.getenv("CENTRAL_PORT", "8080"))
        self.db_path = os.getenv("DB_PATH", "./estacionamento.db")
        self.preco_por_minuto = float(os.getenv("PRECO_POR_MINUTO", "0.15"))
        self.valor_minimo = float(os.getenv("VALOR_MINIMO", "2.00"))
        
        # Estado do estacionamento
        self.veiculos_estacionados: Dict[str, Veiculo] = {}
        self.estacionamento_fechado = False
        self.andar_bloqueado = False
        
        # Servidor TCP
        self.server = None
        self.clientes_conectados = []
        
        # Inicializa banco de dados
        self._inicializar_banco()
    
    def _inicializar_banco(self):
        """Inicializa o banco de dados SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de eventos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    placa TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    confianca_lpr REAL NOT NULL,
                    andar TEXT NOT NULL,
                    status TEXT NOT NULL,
                    valor_calculado REAL,
                    tempo_permanencia_minutos INTEGER,
                    erro_descricao TEXT
                )
            """)
            
            # Tabela de veículos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS veiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    placa TEXT NOT NULL,
                    timestamp_entrada TEXT NOT NULL,
                    timestamp_saida TEXT,
                    andar TEXT NOT NULL,
                    vaga INTEGER,
                    status TEXT NOT NULL,
                    valor_calculado REAL,
                    tempo_permanencia_minutos INTEGER
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Banco de dados inicializado")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco: {e}")
    
    async def iniciar_servidor(self):
        """Inicia o servidor TCP."""
        try:
            self.server = await asyncio.start_server(
                self._handle_cliente,
                self.host,
                self.port
            )
            
            addr = self.server.sockets[0].getsockname()
            logger.info(f"Servidor Central iniciado em {addr[0]}:{addr[1]}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor: {e}")
    
    async def _handle_cliente(self, reader, writer):
        """Manipula conexões de clientes."""
        addr = writer.get_extra_info('peername')
        logger.info(f"Cliente conectado: {addr}")
        self.clientes_conectados.append(writer)
        
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                
                # Decodifica mensagem JSON
                mensagem = data.decode('utf-8').strip()
                logger.debug(f"Mensagem recebida de {addr}: {mensagem}")
                
                try:
                    dados = json.loads(mensagem)
                    resposta = await self._processar_evento(dados)
                    
                    # Envia resposta
                    resposta_json = json.dumps(resposta.dict()) + '\n'
                    writer.write(resposta_json.encode('utf-8'))
                    await writer.drain()
                    
                except json.JSONDecodeError:
                    logger.error(f"Mensagem JSON inválida de {addr}: {mensagem}")
                except Exception as e:
                    logger.error(f"Erro ao processar evento de {addr}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro na conexão com {addr}: {e}")
        finally:
            if writer in self.clientes_conectados:
                self.clientes_conectados.remove(writer)
            writer.close()
            await writer.wait_closed()
            logger.info(f"Cliente desconectado: {addr}")
    
    async def _processar_evento(self, dados: dict) -> EventoResposta:
        """Processa um evento recebido."""
        try:
            # Cria evento a partir dos dados
            evento = Evento(
                placa=dados["placa"],
                tipo=TipoEvento(dados["tipo"]),
                timestamp=datetime.fromisoformat(dados["timestamp"]),
                confianca_lpr=dados["confianca_lpr"],
                andar=dados.get("andar", "terreo")
            )
            
            logger.info(f"Processando evento: {evento.tipo.value} - {evento.placa}")
            
            # Verifica se estacionamento está fechado
            if self.estacionamento_fechado:
                return EventoResposta(
                    evento_id=f"evt_{datetime.now().timestamp()}",
                    sucesso=False,
                    acao="negar_entrada",
                    mensagem="Estacionamento fechado"
                )
            
            # Verifica se andar está bloqueado
            if self.andar_bloqueado and evento.andar == "terreo":
                return EventoResposta(
                    evento_id=f"evt_{datetime.now().timestamp()}",
                    sucesso=False,
                    acao="negar_entrada",
                    mensagem="Andar bloqueado"
                )
            
            # Processa conforme o tipo de evento
            if evento.tipo == TipoEvento.ENTRADA:
                return await self._processar_entrada(evento)
            elif evento.tipo == TipoEvento.SAIDA:
                return await self._processar_saida(evento)
            else:
                return EventoResposta(
                    evento_id=f"evt_{datetime.now().timestamp()}",
                    sucesso=False,
                    acao="erro",
                    mensagem=f"Tipo de evento não suportado: {evento.tipo.value}"
                )
                
        except Exception as e:
            logger.error(f"Erro ao processar evento: {e}")
            return EventoResposta(
                evento_id=f"evt_{datetime.now().timestamp()}",
                sucesso=False,
                acao="erro",
                mensagem=str(e)
            )
    
    async def _processar_entrada(self, evento: Evento) -> EventoResposta:
        """Processa evento de entrada."""
        placa = evento.placa
        
        # Verifica se veículo já está estacionado
        if placa in self.veiculos_estacionados:
            logger.warning(f"Veículo {placa} já está estacionado")
            return EventoResposta(
                evento_id=await self._salvar_evento(evento),
                sucesso=False,
                acao="negar_entrada",
                mensagem="Veículo já está estacionado"
            )
        
        # Cria novo veículo
        veiculo = Veiculo(
            placa=placa,
            timestamp_entrada=evento.timestamp,
            andar=evento.andar
        )
        
        # Adiciona ao estacionamento
        self.veiculos_estacionados[placa] = veiculo
        
        # Salva no banco
        evento.status = StatusEvento.CONCLUIDO
        evento_id = await self._salvar_evento(evento)
        await self._salvar_veiculo(veiculo)
        
        logger.info(f"Entrada autorizada para {placa}")
        
        return EventoResposta(
            evento_id=evento_id,
            sucesso=True,
            acao="abrir_cancela",
            mensagem="Entrada autorizada"
        )
    
    async def _processar_saida(self, evento: Evento) -> EventoResposta:
        """Processa evento de saída."""
        placa = evento.placa
        
        # Verifica se veículo está estacionado
        if placa not in self.veiculos_estacionados:
            logger.warning(f"Veículo {placa} não encontrado no estacionamento")
            return EventoResposta(
                evento_id=await self._salvar_evento(evento),
                sucesso=False,
                acao="negar_saida",
                mensagem="Veículo não encontrado"
            )
        
        # Recupera veículo
        veiculo = self.veiculos_estacionados[placa]
        
        # Calcula valores
        resultado = veiculo.processar_saida(
            evento.timestamp,
            self.preco_por_minuto,
            self.valor_minimo
        )
        
        # Atualiza evento
        evento.valor_calculado = resultado["valor_calculado"]
        evento.tempo_permanencia_minutos = resultado["tempo_permanencia_minutos"]
        evento.status = StatusEvento.CONCLUIDO
        
        # Remove do estacionamento
        del self.veiculos_estacionados[placa]
        
        # Salva no banco
        evento_id = await self._salvar_evento(evento)
        await self._atualizar_veiculo(veiculo)
        
        logger.info(
            f"Saída autorizada para {placa} - "
            f"Tempo: {resultado['tempo_permanencia_minutos']}min - "
            f"Valor: R$ {resultado['valor_calculado']:.2f}"
        )
        
        return EventoResposta(
            evento_id=evento_id,
            sucesso=True,
            acao="cobrar_valor",
            valor=resultado["valor_calculado"],
            tempo_permanencia=resultado["tempo_permanencia_minutos"],
            mensagem=f"Valor a pagar: R$ {resultado['valor_calculado']:.2f}"
        )
    
    async def _salvar_evento(self, evento: Evento) -> str:
        """Salva evento no banco de dados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO eventos (
                    placa, tipo, timestamp, confianca_lpr, andar,
                    status, valor_calculado, tempo_permanencia_minutos, erro_descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evento.placa,
                evento.tipo.value,
                evento.timestamp.isoformat(),
                evento.confianca_lpr,
                evento.andar,
                evento.status.value,
                evento.valor_calculado,
                evento.tempo_permanencia_minutos,
                evento.erro_descricao
            ))
            
            evento_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.debug(f"Evento {evento_id} salvo no banco")
            return str(evento_id)
            
        except Exception as e:
            logger.error(f"Erro ao salvar evento: {e}")
            return f"evt_{datetime.now().timestamp()}"
    
    async def _salvar_veiculo(self, veiculo: Veiculo):
        """Salva veículo no banco de dados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO veiculos (
                    placa, timestamp_entrada, timestamp_saida, andar,
                    vaga, status, valor_calculado, tempo_permanencia_minutos
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                veiculo.placa,
                veiculo.timestamp_entrada.isoformat(),
                veiculo.timestamp_saida.isoformat() if veiculo.timestamp_saida else None,
                veiculo.andar,
                veiculo.vaga,
                veiculo.status.value,
                veiculo.valor_calculado,
                veiculo.tempo_permanencia_minutos
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"Veículo {veiculo.placa} salvo no banco")
            
        except Exception as e:
            logger.error(f"Erro ao salvar veículo: {e}")
    
    async def _atualizar_veiculo(self, veiculo: Veiculo):
        """Atualiza veículo no banco de dados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE veiculos SET
                    timestamp_saida = ?,
                    status = ?,
                    valor_calculado = ?,
                    tempo_permanencia_minutos = ?
                WHERE placa = ? AND timestamp_entrada = ?
            """, (
                veiculo.timestamp_saida.isoformat() if veiculo.timestamp_saida else None,
                veiculo.status.value,
                veiculo.valor_calculado,
                veiculo.tempo_permanencia_minutos,
                veiculo.placa,
                veiculo.timestamp_entrada.isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"Veículo {veiculo.placa} atualizado no banco")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar veículo: {e}")
    
    def fechar_estacionamento(self):
        """Fecha o estacionamento (não permite novas entradas)."""
        self.estacionamento_fechado = True
        logger.info("Estacionamento fechado")
    
    def abrir_estacionamento(self):
        """Abre o estacionamento."""
        self.estacionamento_fechado = False
        logger.info("Estacionamento aberto")
    
    def bloquear_andar(self):
        """Bloqueia o andar térreo."""
        self.andar_bloqueado = True
        logger.info("Andar térreo bloqueado")
    
    def desbloquear_andar(self):
        """Desbloqueia o andar térreo."""
        self.andar_bloqueado = False
        logger.info("Andar térreo desbloqueado")
    
    def obter_estatisticas(self) -> dict:
        """Retorna estatísticas do estacionamento."""
        total_estacionados = len(self.veiculos_estacionados)
        
        # Busca estatísticas do banco
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de entradas hoje
            cursor.execute("""
                SELECT COUNT(*) FROM eventos 
                WHERE tipo = 'entrada' 
                AND date(timestamp) = date('now')
            """)
            entradas_hoje = cursor.fetchone()[0]
            
            # Total de saídas hoje
            cursor.execute("""
                SELECT COUNT(*) FROM eventos 
                WHERE tipo = 'saida' 
                AND date(timestamp) = date('now')
            """)
            saidas_hoje = cursor.fetchone()[0]
            
            # Receita hoje
            cursor.execute("""
                SELECT SUM(valor_calculado) FROM eventos 
                WHERE tipo = 'saida' 
                AND date(timestamp) = date('now')
                AND valor_calculado IS NOT NULL
            """)
            receita_hoje = cursor.fetchone()[0] or 0
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            entradas_hoje = saidas_hoje = receita_hoje = 0
        
        return {
            "veiculos_estacionados": total_estacionados,
            "estacionamento_fechado": self.estacionamento_fechado,
            "andar_bloqueado": self.andar_bloqueado,
            "entradas_hoje": entradas_hoje,
            "saidas_hoje": saidas_hoje,
            "receita_hoje": receita_hoje,
            "clientes_conectados": len(self.clientes_conectados)
        }


async def main():
    """Função principal."""
    servidor = ServidorCentral()
    
    try:
        await servidor.iniciar_servidor()
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro no servidor: {e}")


if __name__ == "__main__":
    asyncio.run(main())
