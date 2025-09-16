"""
Testes para o servidor do térreo.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from src.core.services.lpr_service import LPRService
from src.core.services.cancela_service import CancelaService, TipoCancela, StatusCancela
from src.core.services.placar_service import PlacarService


class TestLPRService:
    """Testes para o serviço LPR."""
    
    @pytest.mark.asyncio
    async def test_captura_simulada(self):
        """Testa captura em modo simulação."""
        lpr = LPRService(modo_simulacao=True)
        placa, confianca = await lpr.capturar_placa()
        
        # Em modo simulação, deve retornar uma placa ou None
        if placa:
            assert len(placa) == 7
            assert 0.0 <= confianca <= 1.0
        else:
            assert confianca == 0.0
    
    @pytest.mark.asyncio
    async def test_validacao_placa(self):
        """Testa validação de placas."""
        lpr = LPRService()
        
        # Placa válida
        assert await lpr.validar_placa("ABC1234")
        
        # Placas inválidas
        assert not await lpr.validar_placa("ABC123")  # Muito curta
        assert not await lpr.validar_placa("AB1234")  # Muito curta
        assert not await lpr.validar_placa("ABCD1234")  # Muito longa
        assert not await lpr.validar_placa("1234ABC")  # Formato errado
        assert not await lpr.validar_placa("")  # Vazia
    
    def test_configuracao_modo(self):
        """Testa configuração de modo."""
        lpr = LPRService(modo_simulacao=True)
        assert lpr.modo_simulacao
        
        lpr.configurar_modo(False)
        assert not lpr.modo_simulacao
    
    def test_estatisticas(self):
        """Testa obtenção de estatísticas."""
        lpr = LPRService()
        stats = lpr.obter_estatisticas()
        
        assert "modo" in stats
        assert "timeout" in stats
        assert "total_placas_simuladas" in stats


class TestCancelaService:
    """Testes para o serviço de cancela."""
    
    def test_criacao_cancela(self):
        """Testa criação de cancela."""
        cancela = CancelaService(
            tipo=TipoCancela.ENTRADA,
            endereco_modbus=1,
            modo_simulacao=True
        )
        
        assert cancela.tipo == TipoCancela.ENTRADA
        assert cancela.endereco_modbus == 1
        assert cancela.modo_simulacao
        assert cancela.status == StatusCancela.FECHADA
    
    @pytest.mark.asyncio
    async def test_abrir_cancela(self):
        """Testa abertura de cancela."""
        cancela = CancelaService(
            tipo=TipoCancela.ENTRADA,
            endereco_modbus=1,
            modo_simulacao=True
        )
        
        resultado = await cancela.abrir_cancela()
        assert resultado
        assert cancela.status == StatusCancela.ABERTA
    
    @pytest.mark.asyncio
    async def test_fechar_cancela(self):
        """Testa fechamento de cancela."""
        cancela = CancelaService(
            tipo=TipoCancela.ENTRADA,
            endereco_modbus=1,
            modo_simulacao=True
        )
        
        # Abre primeiro
        await cancela.abrir_cancela()
        
        # Depois fecha
        resultado = await cancela.fechar_cancela()
        assert resultado
        assert cancela.status == StatusCancela.FECHADA
    
    @pytest.mark.asyncio
    async def test_ciclo_completo(self):
        """Testa ciclo completo da cancela."""
        cancela = CancelaService(
            tipo=TipoCancela.ENTRADA,
            endereco_modbus=1,
            modo_simulacao=True
        )
        
        resultado = await cancela.ciclo_completo()
        assert resultado
        assert cancela.status == StatusCancela.FECHADA
    
    def test_obter_status(self):
        """Testa obtenção de status."""
        cancela = CancelaService(
            tipo=TipoCancela.ENTRADA,
            endereco_modbus=1,
            modo_simulacao=True
        )
        
        status = cancela.obter_status()
        
        assert status["tipo"] == "entrada"
        assert status["status"] == "fechada"
        assert status["endereco_modbus"] == 1
        assert status["modo_simulacao"]


class TestPlacarService:
    """Testes para o serviço de placar."""
    
    def test_criacao_placar(self):
        """Testa criação do placar."""
        placar = PlacarService(
            endereco_modbus=3,
            total_vagas=8,
            modo_simulacao=True
        )
        
        assert placar.endereco_modbus == 3
        assert placar.total_vagas == 8
        assert placar.vagas_livres == 8
        assert len(placar.vagas) == 8
        assert all(not ocupada for ocupada in placar.vagas.values())
    
    def test_ocupar_vaga(self):
        """Testa ocupação de vaga."""
        placar = PlacarService(
            endereco_modbus=3,
            total_vagas=8,
            modo_simulacao=True
        )
        
        # Ocupa vaga 0
        resultado = placar.ocupar_vaga(0)
        assert resultado
        assert placar.vagas[0]
        assert placar.vagas_livres == 7
        
        # Tenta ocupar vaga já ocupada
        resultado = placar.ocupar_vaga(0)
        assert not resultado
        assert placar.vagas_livres == 7
    
    def test_liberar_vaga(self):
        """Testa liberação de vaga."""
        placar = PlacarService(
            endereco_modbus=3,
            total_vagas=8,
            modo_simulacao=True
        )
        
        # Ocupa e depois libera vaga 0
        placar.ocupar_vaga(0)
        resultado = placar.liberar_vaga(0)
        
        assert resultado
        assert not placar.vagas[0]
        assert placar.vagas_livres == 8
        
        # Tenta liberar vaga já livre
        resultado = placar.liberar_vaga(0)
        assert not resultado
        assert placar.vagas_livres == 8
    
    def test_encontrar_vaga_livre(self):
        """Testa busca por vaga livre."""
        placar = PlacarService(
            endereco_modbus=3,
            total_vagas=3,
            modo_simulacao=True
        )
        
        # Todas livres - deve retornar 0
        vaga = placar.encontrar_vaga_livre()
        assert vaga == 0
        
        # Ocupa todas
        for i in range(3):
            placar.ocupar_vaga(i)
        
        # Nenhuma livre - deve retornar -1
        vaga = placar.encontrar_vaga_livre()
        assert vaga == -1
        
        # Libera uma
        placar.liberar_vaga(1)
        vaga = placar.encontrar_vaga_livre()
        assert vaga == 1
    
    def test_estatisticas(self):
        """Testa obtenção de estatísticas."""
        placar = PlacarService(
            endereco_modbus=3,
            total_vagas=4,
            modo_simulacao=True
        )
        
        # Ocupa 2 vagas
        placar.ocupar_vaga(0)
        placar.ocupar_vaga(2)
        
        stats = placar.obter_estatisticas()
        
        assert stats["total_vagas"] == 4
        assert stats["vagas_livres"] == 2
        assert stats["vagas_ocupadas"] == 2
        assert stats["percentual_ocupacao"] == 50.0
        assert not stats["estacionamento_cheio"]
        assert 0 in stats["vagas_ocupadas_numeros"]
        assert 2 in stats["vagas_ocupadas_numeros"]
        assert 1 in stats["vagas_livres_numeros"]
        assert 3 in stats["vagas_livres_numeros"]
    
    def test_estacionamento_cheio(self):
        """Testa detecção de estacionamento cheio."""
        placar = PlacarService(
            endereco_modbus=3,
            total_vagas=2,
            modo_simulacao=True
        )
        
        # Ocupa todas as vagas
        placar.ocupar_vaga(0)
        placar.ocupar_vaga(1)
        
        stats = placar.obter_estatisticas()
        assert stats["estacionamento_cheio"]
        assert stats["vagas_livres"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
