# Sistema de Estacionamento Distribuído

**Projeto**: Sistema de Estacionamento Distribuído  
**Disciplina**: Fundamentos de Sistemas Embarcados  
**Ano**: 2025/2

Sistema de controle de estacionamento inteligente com arquitetura distribuída, utilizando comunicação TCP/IP e protocolo MODBUS para controle de periféricos.

## Introdução

Este repositório apresenta a implementação de um MVP (Minimum Viable Product) de um sistema distribuído para controle de estacionamento inteligente. O projeto foi desenvolvido para a disciplina de Fundamentos de Sistemas Embarcados, demonstrando conceitos de arquitetura distribuída, comunicação TCP/IP e protocolos industriais.

O sistema simula o controle completo de um estacionamento com reconhecimento automático de placas, cálculo de valores por tempo de permanência e controle automatizado de cancelas e placares informativos.

## Tecnologia

A implementação utiliza **Python 3.9+** como linguagem principal, com as seguintes tecnologias:

- **asyncio**: Para programação assíncrona e concorrência
- **TCP/IP**: Comunicação entre servidores distribuídos
- **MODBUS RTU**: Protocolo industrial para controle de hardware
- **SQLite**: Banco de dados local para persistência
- **JSON**: Formato de troca de dados entre servidores

```shell
"O sistema foi projetado com arquitetura modular e distribuída, onde cada andar do estacionamento possui seu próprio servidor de controle, comunicando-se com um servidor central via TCP/IP. A comunicação com hardware (câmeras LPR, cancelas, placares) é realizada via protocolo MODBUS RTU."
```

### Instalando as dependências

Execute os comandos:

```shell
# Crie o ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure o ambiente
cp config/.env.example .env
```

### Executando localmente

Para iniciar o sistema localmente, utilize os comandos em **3 terminais diferentes**:

```shell
# Terminal 1 - Servidor Central
python3 -m src.core.servidor_central

# Terminal 2 - Servidor Térreo
python3 -m src.core.servidor_terreo

# Terminal 3 - Interface de Teste
python3 -m tools.interface_teste
```

## Funcionalidades

- ✅ **Entrada/Saída automatizada** com reconhecimento de placas
- ✅ **Cálculo automático** de tempo e valor de estacionamento
- ✅ **Comunicação distribuída** via TCP/IP entre servidores
- ✅ **Controle de hardware** via protocolo MODBUS RTU
- ✅ **Interface de teste** para simulação completa
- ✅ **Persistência** em banco SQLite
- ✅ **Logs detalhados** para monitoramento

## Arquitetura Lógica 

```
┌─────────────────┐     ┌──────────────────┐
│  Servidor       │◄────┤  Servidor        │
│  Central        │ TCP │  Térreo          │
│  (Gestão)       │     │  (Controle)      │
└─────────────────┘     └──────────────────┘
         │                        │
         │ SQLite                 │ MODBUS RTU
    ┌────▼────┐              ┌────▼────┐
    │  Banco  │              │ Hardware │
    │  Dados  │              │LPR+Placar│
    └─────────┘              └─────────┘
```

## Configuração

Principais variáveis no arquivo `.env`:

```env
MODE=simulation           # simulation | hardware
CENTRAL_HOST=localhost
CENTRAL_PORT=8080
PRECO_POR_MINUTO=0.15
VALOR_MINIMO=2.00
TOTAL_VAGAS=8
```

## Documentação

- **[docs/ARQUITETURA.md](docs/ARQUITETURA.md)** - Arquitetura detalhada do sistema
- **[docs/ESTRUTURA.md](docs/ESTRUTURA.md)** - Organização do projeto