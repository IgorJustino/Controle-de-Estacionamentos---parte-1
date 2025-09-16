"""
Interface de teste para o sistema de estacionamento.
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tools.simulador import SimuladorEstacionamento


class InterfaceTeste:
    """Interface de teste com menu interativo."""
    
    def __init__(self):
        self.simulador = SimuladorEstacionamento()
        self.historico: List[Dict] = []
    
    def limpar_tela(self):
        """Limpa a tela do terminal."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def exibir_header(self):
        """Exibe cabeçalho da aplicação."""
        print("=" * 60)
        print("🚗 SISTEMA DE ESTACIONAMENTO - INTERFACE DE TESTE")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print()
    
    def exibir_status(self):
        """Exibe status atual do sistema."""
        status = self.simulador.obter_status()
        
        print("📊 STATUS ATUAL:")
        print(f"   🚗 Veículos estacionados: {status['veiculos_estacionados']}")
        if status['placas_estacionadas']:
            print(f"   📋 Placas: {', '.join(status['placas_estacionadas'])}")
        print()
    
    def exibir_menu(self):
        """Exibe menu principal."""
        print("🎮 OPÇÕES DISPONÍVEIS:")
        print("   1️⃣  Simular Entrada")
        print("   2️⃣  Simular Saída")
        print("   3️⃣  Fluxo Completo (Entradas + Saídas)")
        print("   4️⃣  Teste de Carga (Simulação Contínua)")
        print("   5️⃣  Ver Histórico")
        print("   6️⃣  Demonstração Automática")
        print("   7️⃣  Teste de Erro (Placa Inválida)")
        print("   0️⃣  Sair")
        print()
    
    def registrar_evento(self, tipo: str, placa: str, resultado: Dict):
        """Registra evento no histórico."""
        self.historico.append({
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "placa": placa,
            "sucesso": resultado.get("sucesso", False),
            "mensagem": resultado.get("mensagem", ""),
            "valor": resultado.get("valor"),
            "tempo": resultado.get("tempo_permanencia")
        })
    
    async def simular_entrada_interativa(self):
        """Simula entrada com interface interativa."""
        print("🎯 SIMULAÇÃO DE ENTRADA")
        print("-" * 30)
        
        placa = input("Digite a placa (ou ENTER para aleatória): ").strip().upper()
        if not placa:
            placa = None
        
        print("🔄 Processando entrada...")
        resultado = await self.simulador.simular_entrada(placa)
        
        self.registrar_evento("entrada", placa or "ALEATÓRIA", resultado)
        
        if resultado.get("sucesso"):
            print(f"✅ Entrada autorizada!")
            print(f"   🏷️  Placa: {placa}")
            print(f"   ⏰ Horário: {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"❌ Entrada negada!")
            print(f"   📝 Motivo: {resultado.get('mensagem', 'Erro desconhecido')}")
        
        input("\nPressione ENTER para continuar...")
    
    async def simular_saida_interativa(self):
        """Simula saída com interface interativa."""
        print("🎯 SIMULAÇÃO DE SAÍDA")
        print("-" * 30)
        
        status = self.simulador.obter_status()
        if not status['placas_estacionadas']:
            print("❌ Nenhum veículo estacionado!")
            input("\nPressione ENTER para continuar...")
            return
        
        print("🚗 Veículos estacionados:")
        for i, placa in enumerate(status['placas_estacionadas'], 1):
            print(f"   {i}. {placa}")
        
        opcao = input("\nEscolha um veículo (número) ou digite uma placa: ").strip()
        
        if opcao.isdigit():
            idx = int(opcao) - 1
            if 0 <= idx < len(status['placas_estacionadas']):
                placa = status['placas_estacionadas'][idx]
            else:
                print("❌ Opção inválida!")
                input("\nPressione ENTER para continuar...")
                return
        else:
            placa = opcao.upper() if opcao else None
        
        print("🔄 Processando saída...")
        resultado = await self.simulador.simular_saida(placa)
        
        self.registrar_evento("saida", placa or "ALEATÓRIA", resultado)
        
        if resultado.get("sucesso"):
            valor = resultado.get("valor", 0)
            tempo = resultado.get("tempo_permanencia", 0)
            print(f"✅ Saída autorizada!")
            print(f"   🏷️  Placa: {placa}")
            print(f"   ⏰ Tempo: {tempo} minutos")
            print(f"   💰 Valor: R$ {valor:.2f}")
        else:
            print(f"❌ Saída negada!")
            print(f"   📝 Motivo: {resultado.get('mensagem', 'Erro desconhecido')}")
        
        input("\nPressione ENTER para continuar...")
    
    async def fluxo_completo_interativo(self):
        """Executa fluxo completo interativo."""
        print("🎯 FLUXO COMPLETO")
        print("-" * 30)
        
        try:
            num_str = input("Número de veículos (padrão 3): ").strip()
            num_veiculos = int(num_str) if num_str.isdigit() else 3
        except ValueError:
            num_veiculos = 3
        
        print(f"🔄 Simulando {num_veiculos} veículos...")
        print("\n📥 ENTRADAS:")
        
        # Simula entradas
        for i in range(num_veiculos):
            resultado = await self.simulador.simular_entrada()
            if resultado.get("sucesso"):
                print(f"   ✅ Veículo {i+1}: Entrada autorizada")
            else:
                print(f"   ❌ Veículo {i+1}: {resultado.get('mensagem', 'Erro')}")
            await asyncio.sleep(1)
        
        print(f"\n⏰ Aguardando 3 segundos...")
        await asyncio.sleep(3)
        
        # Simula algumas saídas
        status = self.simulador.obter_status()
        num_saidas = min(2, len(status['placas_estacionadas']))
        
        if num_saidas > 0:
            print(f"\n📤 SAÍDAS ({num_saidas} veículos):")
            for i in range(num_saidas):
                resultado = await self.simulador.simular_saida()
                if resultado.get("sucesso"):
                    valor = resultado.get("valor", 0)
                    print(f"   ✅ Saída {i+1}: R$ {valor:.2f}")
                else:
                    print(f"   ❌ Saída {i+1}: {resultado.get('mensagem', 'Erro')}")
                await asyncio.sleep(1)
        
        status_final = self.simulador.obter_status()
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   🚗 Veículos restantes: {status_final['veiculos_estacionados']}")
        
        input("\nPressione ENTER para continuar...")
    
    async def teste_carga_continua(self):
        """Executa teste de carga contínua."""
        print("🎯 TESTE DE CARGA CONTÍNUA")
        print("-" * 30)
        
        try:
            intervalo_str = input("Intervalo entre eventos em segundos (padrão 5): ").strip()
            intervalo = float(intervalo_str) if intervalo_str else 5.0
        except ValueError:
            intervalo = 5.0
        
        print(f"🔄 Iniciando teste contínuo (intervalo: {intervalo}s)")
        print("⚠️  Pressione Ctrl+C para parar")
        print()
        
        contador = 0
        try:
            while True:
                contador += 1
                status = self.simulador.obter_status()
                
                # Decide entre entrada ou saída
                if status['veiculos_estacionados'] == 0 or (contador % 3 != 0):
                    print(f"📥 Evento {contador}: Simulando entrada...")
                    resultado = await self.simulador.simular_entrada()
                    tipo = "entrada"
                else:
                    print(f"📤 Evento {contador}: Simulando saída...")
                    resultado = await self.simulador.simular_saida()
                    tipo = "saída"
                
                if resultado.get("sucesso"):
                    if tipo == "saída":
                        valor = resultado.get("valor", 0)
                        print(f"   ✅ {tipo.title()} autorizada - R$ {valor:.2f}")
                    else:
                        print(f"   ✅ {tipo.title()} autorizada")
                else:
                    print(f"   ❌ {tipo.title()} negada: {resultado.get('mensagem', 'Erro')}")
                
                # Mostra status a cada 5 eventos
                if contador % 5 == 0:
                    status = self.simulador.obter_status()
                    print(f"📊 Status: {status['veiculos_estacionados']} veículos estacionados")
                
                await asyncio.sleep(intervalo)
                
        except KeyboardInterrupt:
            print(f"\n⏹️  Teste parado após {contador} eventos")
            status = self.simulador.obter_status()
            print(f"📊 Status final: {status['veiculos_estacionados']} veículos estacionados")
        
        input("\nPressione ENTER para continuar...")
    
    def exibir_historico(self):
        """Exibe histórico de eventos."""
        print("🎯 HISTÓRICO DE EVENTOS")
        print("-" * 30)
        
        if not self.historico:
            print("📭 Nenhum evento registrado ainda.")
            input("\nPressione ENTER para continuar...")
            return
        
        print(f"📊 Total de eventos: {len(self.historico)}")
        print()
        
        # Mostra últimos 10 eventos
        eventos_recentes = self.historico[-10:]
        
        for i, evento in enumerate(eventos_recentes, 1):
            timestamp = datetime.fromisoformat(evento['timestamp'])
            status_icon = "✅" if evento['sucesso'] else "❌"
            tipo_icon = "📥" if evento['tipo'] == "entrada" else "📤"
            
            print(f"{i:2d}. {tipo_icon} {status_icon} {evento['tipo'].upper()}")
            print(f"     ⏰ {timestamp.strftime('%H:%M:%S')}")
            print(f"     🏷️  {evento['placa']}")
            
            if evento['valor']:
                print(f"     💰 R$ {evento['valor']:.2f} ({evento['tempo']} min)")
            
            if not evento['sucesso']:
                print(f"     📝 {evento['mensagem']}")
            print()
        
        if len(self.historico) > 10:
            print(f"... e mais {len(self.historico) - 10} eventos anteriores")
        
        input("\nPressione ENTER para continuar...")
    
    async def demonstracao_automatica(self):
        """Executa uma demonstração automática."""
        print("🎯 DEMONSTRAÇÃO AUTOMÁTICA")
        print("-" * 30)
        print("🎬 Iniciando demonstração do sistema completo...")
        print()
        
        # Cenário 1: Entrada normal
        print("📥 Cenário 1: Entrada de veículo")
        resultado = await self.simulador.simular_entrada("ABC1234")
        await asyncio.sleep(2)
        
        # Cenário 2: Mais entradas
        print("📥 Cenário 2: Múltiplas entradas")
        for placa in ["DEF5678", "GHI9012"]:
            await self.simulador.simular_entrada(placa)
            await asyncio.sleep(1)
        
        print("⏰ Aguardando permanência...")
        await asyncio.sleep(3)
        
        # Cenário 3: Saídas com cobrança
        print("📤 Cenário 3: Saídas com cobrança")
        for _ in range(2):
            resultado = await self.simulador.simular_saida()
            if resultado.get("sucesso"):
                valor = resultado.get("valor", 0)
                print(f"   💰 Valor cobrado: R$ {valor:.2f}")
            await asyncio.sleep(2)
        
        # Cenário 4: Tentativa de saída de veículo não estacionado
        print("📤 Cenário 4: Tentativa de saída inválida")
        await self.simulador.simular_saida("XYZ9999")
        await asyncio.sleep(2)
        
        print("✅ Demonstração concluída!")
        status = self.simulador.obter_status()
        print(f"📊 Status final: {status['veiculos_estacionados']} veículos estacionados")
        
        input("\nPressione ENTER para continuar...")
    
    async def teste_erro(self):
        """Testa cenários de erro."""
        print("🎯 TESTE DE CENÁRIOS DE ERRO")
        print("-" * 30)
        
        print("❌ Testando placa inválida...")
        # Simula erro criando evento diretamente
        resultado = {"sucesso": False, "mensagem": "Placa inválida"}
        print("   📝 Resultado: Placa rejeitada pelo sistema")
        
        print("\n❌ Testando veículo já estacionado...")
        # Primeiro estaciona um veículo
        await self.simulador.simular_entrada("TEST123")
        # Tenta estacionar novamente
        resultado = await self.simulador.simular_entrada("TEST123")
        
        print("\n❌ Testando saída de veículo não estacionado...")
        resultado = await self.simulador.simular_saida("INEXISTENTE")
        
        print("\n✅ Testes de erro concluídos!")
        input("\nPressione ENTER para continuar...")
    
    async def executar(self):
        """Executa a interface principal."""
        while True:
            try:
                self.limpar_tela()
                self.exibir_header()
                self.exibir_status()
                self.exibir_menu()
                
                opcao = input("🎮 Escolha uma opção: ").strip()
                print()
                
                if opcao == "1":
                    await self.simular_entrada_interativa()
                elif opcao == "2":
                    await self.simular_saida_interativa()
                elif opcao == "3":
                    await self.fluxo_completo_interativo()
                elif opcao == "4":
                    await self.teste_carga_continua()
                elif opcao == "5":
                    self.exibir_historico()
                elif opcao == "6":
                    await self.demonstracao_automatica()
                elif opcao == "7":
                    await self.teste_erro()
                elif opcao == "0":
                    print("👋 Encerrando interface de teste...")
                    break
                else:
                    print("❌ Opção inválida!")
                    await asyncio.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interface encerrada pelo usuário.")
                break
            except Exception as e:
                print(f"❌ Erro na interface: {e}")
                input("\nPressione ENTER para continuar...")


async def main():
    """Função principal."""
    print("🚀 Iniciando Interface de Teste...")
    print("⚠️  Certifique-se de que o Servidor Central esteja rodando!")
    
    # Aguarda um pouco para o usuário ler
    await asyncio.sleep(2)
    
    interface = InterfaceTeste()
    await interface.executar()


if __name__ == "__main__":
    asyncio.run(main())
