"""
Simulador para testes do sistema de estacionamento.
"""
import asyncio
import json
import logging
import random
import sys
import os
from datetime import datetime
from typing import List, Dict

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.models.evento import Evento, TipoEvento

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimuladorEstacionamento:
    """Simulador para testes do sistema."""
    
    def __init__(self, central_host: str = "localhost", central_port: int = 8080):
        self.central_host = central_host
        self.central_port = central_port
        self.placas_teste = [
            "ABC1234", "DEF5678", "GHI9012", "JKL3456", "MNO7890",
            "PQR1234", "STU5678", "VWX9012", "YZA3456", "BCD7890"
        ]
        self.veiculos_estacionados: List[str] = []
    
    async def simular_entrada(self, placa: str = None) -> Dict:
        """Simula entrada de um veículo."""
        if not placa:
            placa = random.choice([p for p in self.placas_teste if p not in self.veiculos_estacionados])
        
        evento = Evento(
            placa=placa,
            tipo=TipoEvento.ENTRADA,
            timestamp=datetime.now(),
            confianca_lpr=random.uniform(0.8, 0.98),
            andar="terreo"
        )
        
        logger.info(f"Simulando entrada: {placa}")
        resposta = await self._enviar_evento(evento)
        
        if resposta and resposta.get("sucesso"):
            self.veiculos_estacionados.append(placa)
            logger.info(f"✅ Entrada autorizada: {placa}")
        else:
            logger.warning(f"❌ Entrada negada: {placa} - {resposta.get('mensagem', 'Erro')}")
        
        return resposta
    
    async def simular_saida(self, placa: str = None) -> Dict:
        """Simula saída de um veículo."""
        if not placa:
            if not self.veiculos_estacionados:
                logger.warning("Nenhum veículo estacionado para simular saída")
                return {"sucesso": False, "mensagem": "Nenhum veículo estacionado"}
            placa = random.choice(self.veiculos_estacionados)
        
        if placa not in self.veiculos_estacionados:
            logger.warning(f"Veículo {placa} não está estacionado")
            return {"sucesso": False, "mensagem": "Veículo não está estacionado"}
        
        evento = Evento(
            placa=placa,
            tipo=TipoEvento.SAIDA,
            timestamp=datetime.now(),
            confianca_lpr=random.uniform(0.8, 0.98),
            andar="terreo"
        )
        
        logger.info(f"Simulando saída: {placa}")
        resposta = await self._enviar_evento(evento)
        
        if resposta and resposta.get("sucesso"):
            self.veiculos_estacionados.remove(placa)
            valor = resposta.get("valor", 0)
            tempo = resposta.get("tempo_permanencia", 0)
            logger.info(f"✅ Saída autorizada: {placa} - R$ {valor:.2f} ({tempo} min)")
        else:
            logger.warning(f"❌ Saída negada: {placa} - {resposta.get('mensagem', 'Erro')}")
        
        return resposta
    
    async def _enviar_evento(self, evento: Evento) -> Dict:
        """Envia evento ao servidor central."""
        try:
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
            return resposta
            
        except Exception as e:
            logger.error(f"Erro ao comunicar com servidor central: {e}")
            return {"sucesso": False, "mensagem": str(e)}
    
    async def simular_fluxo_completo(self, num_veiculos: int = 5):
        """Simula um fluxo completo de entradas e saídas."""
        logger.info(f"Iniciando simulação com {num_veiculos} veículos")
        
        # Simula entradas
        for i in range(num_veiculos):
            await self.simular_entrada()
            await asyncio.sleep(random.uniform(1, 3))
        
        logger.info(f"Veículos estacionados: {len(self.veiculos_estacionados)}")
        
        # Aguarda um pouco
        await asyncio.sleep(5)
        
        # Simula algumas saídas
        num_saidas = random.randint(1, len(self.veiculos_estacionados))
        for i in range(num_saidas):
            await self.simular_saida()
            await asyncio.sleep(random.uniform(1, 3))
        
        logger.info(f"Simulação concluída. Veículos restantes: {len(self.veiculos_estacionados)}")
        
        return {
            "veiculos_restantes": len(self.veiculos_estacionados),
            "placas_restantes": self.veiculos_estacionados.copy()
        }
    
    async def simular_carga_continua(self, intervalo: float = 10):
        """Simula carga contínua no sistema."""
        logger.info(f"Iniciando simulação contínua (intervalo: {intervalo}s)")
        
        while True:
            try:
                # Decide aleatoriamente entre entrada ou saída
                if len(self.veiculos_estacionados) == 0 or random.random() < 0.6:
                    # Prioriza entradas se não há veículos ou 60% de chance
                    await self.simular_entrada()
                else:
                    # Simula saída
                    await self.simular_saida()
                
                await asyncio.sleep(intervalo)
                
            except KeyboardInterrupt:
                logger.info("Simulação interrompida pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro na simulação: {e}")
                await asyncio.sleep(5)
    
    def obter_status(self) -> Dict:
        """Retorna status atual da simulação."""
        return {
            "veiculos_estacionados": len(self.veiculos_estacionados),
            "placas_estacionadas": self.veiculos_estacionados.copy(),
            "total_placas_teste": len(self.placas_teste)
        }


async def main():
    """Função principal do simulador."""
    simulador = SimuladorEstacionamento()
    
    print("=== Simulador de Estacionamento ===")
    print("1. Simular entrada")
    print("2. Simular saída")
    print("3. Fluxo completo")
    print("4. Carga contínua")
    print("5. Status")
    print("0. Sair")
    
    while True:
        try:
            opcao = input("\nEscolha uma opção: ").strip()
            
            if opcao == "1":
                placa = input("Placa (deixe vazio para aleatória): ").strip() or None
                await simulador.simular_entrada(placa)
            
            elif opcao == "2":
                placa = input("Placa (deixe vazio para aleatória): ").strip() or None
                await simulador.simular_saida(placa)
            
            elif opcao == "3":
                num = input("Número de veículos (padrão 5): ").strip()
                num_veiculos = int(num) if num.isdigit() else 5
                resultado = await simulador.simular_fluxo_completo(num_veiculos)
                print(f"Resultado: {resultado}")
            
            elif opcao == "4":
                intervalo = input("Intervalo em segundos (padrão 10): ").strip()
                intervalo = float(intervalo) if intervalo else 10
                await simulador.simular_carga_continua(intervalo)
            
            elif opcao == "5":
                status = simulador.obter_status()
                print(f"Status: {json.dumps(status, indent=2)}")
            
            elif opcao == "0":
                print("Saindo...")
                break
            
            else:
                print("Opção inválida!")
                
        except KeyboardInterrupt:
            print("\nSaindo...")
            break
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(main())
