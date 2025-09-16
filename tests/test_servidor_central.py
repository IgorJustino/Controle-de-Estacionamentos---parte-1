"""
Testes para o servidor central.
"""
import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import patch

from src.core.models.evento import Evento, TipoEvento
from src.core.models.veiculo import Veiculo


class TestServidorCentral:
    """Testes para o servidor central."""
    
    def setup_method(self):
        """Configuração para cada teste."""
        # Usa banco temporário para testes
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock das variáveis de ambiente
        self.env_patcher = patch.dict(os.environ, {
            'DB_PATH': self.temp_db.name,
            'PRECO_POR_MINUTO': '0.15',
            'VALOR_MINIMO': '2.00'
        })
        self.env_patcher.start()
    
    def teardown_method(self):
        """Limpeza após cada teste."""
        self.env_patcher.stop()
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    def test_evento_criacao(self):
        """Testa criação de evento."""
        evento = Evento(
            placa="ABC1234",
            tipo=TipoEvento.ENTRADA,
            timestamp=datetime.now(),
            confianca_lpr=0.95,
            andar="terreo"
        )
        
        assert evento.placa == "ABC1234"
        assert evento.tipo == TipoEvento.ENTRADA
        assert evento.confianca_lpr == 0.95
        assert evento.andar == "terreo"
    
    def test_evento_to_dict(self):
        """Testa conversão de evento para dicionário."""
        timestamp = datetime.now()
        evento = Evento(
            placa="ABC1234",
            tipo=TipoEvento.ENTRADA,
            timestamp=timestamp,
            confianca_lpr=0.95,
            andar="terreo"
        )
        
        dados = evento.to_dict()
        
        assert dados["placa"] == "ABC1234"
        assert dados["tipo"] == "entrada"
        assert dados["timestamp"] == timestamp.isoformat()
        assert dados["confianca_lpr"] == 0.95
        assert dados["andar"] == "terreo"
    
    def test_evento_from_dict(self):
        """Testa criação de evento a partir de dicionário."""
        timestamp = datetime.now()
        dados = {
            "placa": "ABC1234",
            "tipo": "entrada",
            "timestamp": timestamp.isoformat(),
            "confianca_lpr": 0.95,
            "andar": "terreo"
        }
        
        evento = Evento.from_dict(dados)
        
        assert evento.placa == "ABC1234"
        assert evento.tipo == TipoEvento.ENTRADA
        assert evento.timestamp == timestamp
        assert evento.confianca_lpr == 0.95
        assert evento.andar == "terreo"
    
    def test_veiculo_calculo_tempo(self):
        """Testa cálculo de tempo de permanência."""
        entrada = datetime(2024, 1, 1, 10, 0, 0)
        saida = datetime(2024, 1, 1, 10, 65, 30)  # 65 min e 30 seg
        
        veiculo = Veiculo("ABC1234", entrada)
        tempo = veiculo.calcular_tempo_permanencia(saida)
        
        # Deve arredondar para cima
        assert tempo == 66
    
    def test_veiculo_calculo_valor(self):
        """Testa cálculo de valor."""
        veiculo = Veiculo("ABC1234", datetime.now())
        veiculo.tempo_permanencia_minutos = 10
        
        # Teste com valor abaixo do mínimo
        valor = veiculo.calcular_valor(0.15, 2.00)
        assert valor == 2.00  # Valor mínimo
        
        # Teste com valor acima do mínimo
        veiculo.tempo_permanencia_minutos = 20
        valor = veiculo.calcular_valor(0.15, 2.00)
        assert valor == 3.00  # 20 * 0.15
    
    def test_veiculo_processar_saida(self):
        """Testa processamento de saída."""
        entrada = datetime(2024, 1, 1, 10, 0, 0)
        saida = datetime(2024, 1, 1, 10, 30, 0)  # 30 minutos
        
        veiculo = Veiculo("ABC1234", entrada)
        resultado = veiculo.processar_saida(saida, 0.15, 2.00)
        
        assert resultado["placa"] == "ABC1234"
        assert resultado["tempo_permanencia_minutos"] == 30
        assert resultado["valor_calculado"] == 4.50  # 30 * 0.15
        assert "timestamp_entrada" in resultado
        assert "timestamp_saida" in resultado


@pytest.mark.asyncio
class TestServidorCentralAsync:
    """Testes assíncronos para o servidor central."""
    
    async def test_servidor_inicializacao(self):
        """Testa inicialização do servidor."""
        from servidor_central import ServidorCentral
        
        with patch.dict(os.environ, {
            'DB_PATH': ':memory:',
            'CENTRAL_PORT': '0'  # Usa porta aleatória
        }):
            servidor = ServidorCentral()
            assert servidor.preco_por_minuto == 0.15
            assert servidor.valor_minimo == 2.00
            assert not servidor.estacionamento_fechado
            assert not servidor.andar_bloqueado


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
