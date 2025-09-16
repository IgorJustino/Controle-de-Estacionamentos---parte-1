# 📁 Estrutura do Projeto - Sistem### 🛠️ tools/ - Ferramentas

- **simulador.py**: Simulador para testes sem hardware (executável)
- **interface_teste.py**: Interface interativa para demonstrações (executável)

### 📚 docs/ - Documentação

- **PROJETO_FINAL.md**: Resumo geral do projeto
- **DEMONSTRACAO.md**: Roteiro detalhado para demonstração
- **EXECUCAO.md**: Guia rápido de execução
- **ESTRUTURA.md**: Este documentoo

## 🏗️ Organização dos Arquivos

O projeto foi organizado em uma estrutura modular e profissional:

### 📦 Diretórios Principais

```
sistema-estacionamento/
├── 📁 src/                    # Código fonte principal
├── 📁 tools/                  # Ferramentas e utilitários
├── 📁 docs/                  # Documentação
├── 📁 config/                # Configurações
├── 📁 tests/                 # Testes automatizados
├── 📁 logs/                  # Arquivos de log
├── 📁 data/                  # Dados persistentes
├── 📁 venv/                  # Ambiente virtual
├── 📄 requirements.txt      # Dependências Python
├── 📄 README.md            # Documentação principal
└── 📄 .gitignore           # Arquivos ignorados pelo Git
```

### 🎯 src/ - Código Principal

#### src/core/ - Componentes Centrais
- **models/**: Modelos de dados (Evento, Veiculo)
- **services/**: Serviços (LPR, Cancela, Placar)
- **servidor_central.py**: Servidor principal de gestão
- **servidor_terreo.py**: Servidor distribuído de controle

#### src/clients/ - Clientes de Comunicação
- **modbus_client.py**: Cliente para comunicação MODBUS

### � bin/ - Pontos de Entrada

- **main_central.py**: Ponto de entrada para o Servidor Central
- **main_terreo.py**: Ponto de entrada para o Servidor do Térreo
- **main_simulador.py**: Ponto de entrada para o Simulador
- **main_interface.py**: Ponto de entrada para a Interface de Teste

### �🛠️ tools/ - Ferramentas

- **simulador.py**: Simulador para testes sem hardware
- **interface_teste.py**: Interface interativa para demonstrações

### � docs/ - Documentação

- **PROJETO_FINAL.md**: Resumo geral do projeto
- **DEMONSTRACAO.md**: Roteiro detalhado para demonstração
- **EXECUCAO.md**: Guia rápido de execução
- **ESTRUTURA.md**: Este documento

### ⚙️ config/ - Configurações

- **.env.example**: Modelo de configuração com todas as variáveis

### 🧪 tests/ - Testes

- **test_servidor_central.py**: Testes do servidor central
- **test_servidor_terreo.py**: Testes dos serviços

### 📊 data/ - Dados

- Local para banco de dados SQLite e outros dados persistentes

### 📝 logs/ - Logs

- Arquivos de log organizados por componente

## 🚀 Pontos de Entrada

### Arquivos Principais (no diretório raiz):

- **main_central.py**: Inicia o Servidor Central
- **main_terreo.py**: Inicia o Servidor do Térreo  
- **main_interface.py**: Inicia a Interface de Teste
- **main_simulador.py**: Inicia o Simulador
- **start.sh**: Script unificado de inicialização

## 🔧 Vantagens da Nova Estrutura

### ✅ Organização Profissional
- Separação clara de responsabilidades
- Estrutura escalável e manutenível
- Fácil navegação e entendimento

### ✅ Modularidade
- Componentes bem definidos
- Imports organizados
- Testabilidade aprimorada

### ✅ Facilidade de Uso
- Pontos de entrada claros
- Scripts de automação
- Documentação organizada

### ✅ Ambiente Limpo
- Configurações centralizadas
- Dados separados do código
- Logs organizados

## 📋 Como Usar

### Execução Simples:
```bash
./start.sh central     # Servidor Central
./start.sh interface   # Interface de Teste
```

### Execução Direta:
```bash
python3 main_central.py    # Servidor Central
python3 main_interface.py  # Interface de Teste
```

### Desenvolvimento:
```bash
./start.sh install    # Instala dependências
./start.sh test       # Executa testes
```

## 🎯 Arquivos de Configuração

- **.env**: Configurações locais (criado automaticamente)
- **config/.env.example**: Modelo de configuração
- **requirements.txt**: Dependências Python

## 📈 Benefícios para Desenvolvimento

1. **Manutenibilidade**: Código organizado e modular
2. **Escalabilidade**: Fácil adição de novos componentes
3. **Testabilidade**: Testes organizados por módulo
4. **Documentação**: Docs centralizadas e atualizadas
5. **Deploy**: Estrutura profissional para produção

---

**🎉 Resultado**: Projeto organizado profissionalmente, mantendo toda a funcionalidade do MVP com estrutura escalável e manutenível!
