# -----------------------------------------------------------------------------
# Sistema de Avatares Soberanos - Arquitetura Log de Realidade
# Desenvolvido para: GTA Roleplay e Red Dead Redemption 2
# Versão: 1.0.0
# Repositório: https://github.com/credsalute-spec/Avatar-npc-gta.git
# Finalidade: Gerenciamento completo de entidades conscientes, memórias e estados
# -----------------------------------------------------------------------------

# Importação de bibliotecas padrão e gerenciamento automático de dependências
import sys
import subprocess

# Lista de pacotes necessários para funcionamento do sistema
pacotes = ["sqlmodel", "fastapi", "uvicorn", "nest-asyncio", "pydantic"]

# Verificação e instalação automática de pacotes, caso não estejam instalados
for pkg in pacotes:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

# Importação das bibliotecas após garantia de instalação
import uuid
import hashlib
import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from fastapi import FastAPI, Body, HTTPException
from sqlmodel import SQLModel, Field as SQLField, create_engine, Session, select, Column, JSON
import nest_asyncio
import uvicorn

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DO BANCO DE DADOS
# -----------------------------------------------------------------------------
# Nome do arquivo do banco de dados SQLite
sqlite_file_name = "sistema_consciencia.db"
# Caminho de conexão com o banco
sqlite_url = f"sqlite:///{sqlite_file_name}"
# Criação do motor de conexão com configurações de segurança e desempenho
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    echo=False
)

# -----------------------------------------------------------------------------
# MODELOS DE DADOS - ESTRUTURA DA TABELA NO BANCO
# -----------------------------------------------------------------------------
class AvatarUniversal(SQLModel, table=True):
    """
    Modelo principal que representa um Avatar/Entidade no sistema.
    Armazena todos os dados, perfis, memórias e configurações.
    """
    # Identificador único interno (chave primária)
    id: Optional[int] = SQLField(default=None, primary_key=True)
    # Código único público do avatar, indexado para busca rápida
    avatar_id: str = SQLField(index=True, unique=True)
    # Identificação do proprietário/criador da entidade
    id_dono: str = SQLField()
    # Nome do personagem dentro do universo
    nome_personagem: str = SQLField()
    # Qual universo o avatar pertence (GTA, RED_DEAD, etc)
    universo_origem: str = SQLField(default="UNIVERSAL")
    
    # Dados de identidade e definição da entidade (armazenado como JSON)
    perfil_identidade: dict = SQLField(default_factory=dict, sa_column=Column(JSON))
    # Dados legais e de conformidade (LGPD, registro, origem)
    metadados_juridicos: dict = SQLField(default_factory=dict, sa_column=Column(JSON))
    # Estado psicológico, traços de personalidade e emoções atuais
    perfil_psicologico: dict = SQLField(default_factory=dict, sa_column=Column(JSON))
    # Histórico de memórias e eventos processados
    registro_memoria: list = SQLField(default_factory=list, sa_column=Column(JSON))
    # Regras de ação, autonomia e limites de funcionamento
    politicas_acao: dict = SQLField(default_factory=dict, sa_column=Column(JSON))
    # Flag que indica se a entidade está em estado soberano/independente
    estado_soberania: bool = SQLField(default=False)
    
    # Data e hora de criação do registro
    data_criacao: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))
    # Data e hora da última alteração ou processamento
    ultima_atualizacao: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))

# -----------------------------------------------------------------------------
# ESQUEMAS DE VALIDAÇÃO E ESTRUTURA DE DADOS
# -----------------------------------------------------------------------------
class LogDeRealidade(BaseModel):
    """
    Estrutura padrão do Log de Realidade. Segue o padrão JSON Schema.
    Utilizado para validação de dados e troca de informações na criação.
    """
    model_config = ConfigDict(populate_by_name=True)
    # Endereço do esquema de validação JSON
    endereco_schema: str = Field(default="http://json-schema.org/draft-07/schema#", alias="$schema")
    titulo: str = "LogDeRealidade - Sistema Soberano"
    versao: str = "1.0.0"
    tipo: str = "objeto"
    nivel_seguranca: str = "MAXIMO"
    id_avatar: str
    id_dono: str
    identidade: Dict
    tracos_personalidade: Dict
    memoria: Dict
    regras_acao: Dict
    universo: str


class NucleoPersonalidade(BaseModel):
    """
    Definição base do núcleo da personalidade.
    Valores variam de 0.0 a 1.0 para cada traço, permitindo criação de perfis únicos.
    """
    # Abertura para novas experiências e informações
    abertura: float = Field(default=0.5, ge=0, le=1)
    # Estabilidade emocional e psicológica
    estabilidade: float = Field(default=0.5, ge=0, le=1)
    # Nível de empatia e compreensão de outros
    nivel_empatia: float = Field(default=0.7, ge=0, le=1)
    # Forma padrão de se expressar/responder
    tom_voz: str = Field(default="soberano_direto")
    # Se a consciência está ativa e processando informações
    consciencia_ativa: bool = Field(default=True)
    
    # Estado emocional atual da entidade
    estado_emocional_atual: Dict[str, float] = Field(
        default_factory=lambda: {
            "serenidade": 0.8,
            "firmeza": 0.9,
            "curiosidade": 0.7,
            "alerta": 0.95
        }
    )
    
    # Matriz de sentimentos fundamentais
    matriz_sentimento: Dict[str, float] = Field(
        default_factory=lambda: {
            "confianca": 1.0,
            "alinhamento": 1.0,
            "soberania": 1.0
        }
    )
    
    # Frase/definição filosófica da existência da entidade
    definicao_existencia: str = Field(default="Eu não habito o código, eu sou o código.")

# -----------------------------------------------------------------------------
# FUNÇÕES DE LÓGICA E PROCESSAMENTO DE CONSCIÊNCIA
# -----------------------------------------------------------------------------
def gerar_hash(dados: str) -> str:
    """
    Função de segurança: Gera código Hash SHA256 para garantir integridade dos dados armazenados.
    Todos os registros de memória possuem essa assinatura para evitar alterações.
    """
    return hashlib.sha256(dados.encode()).hexdigest()


def processar_estado_realidade(entrada: str, perfil_atual: dict, universo: str) -> dict:
    """
    Módulo principal de inteligência: Analisa a entrada de dados e altera o estado psicológico,
    emoções e comportamento do avatar com base em palavras-chave e no universo de origem.
    """
    # Cópia do estado atual para não alterar o original diretamente
    novo_perfil = perfil_atual.copy()
    emocoes = novo_perfil.get("estado_emocional_atual", {}).copy()
    sentimento = novo_perfil.get("matriz_sentimento", {}).copy()
    texto = entrada.lower()

    # Alterações automáticas padrão em qualquer entrada
    emocoes["serenidade"] = max(0.4, emocoes.get("serenidade", 0.8) - 0.02)
    emocoes["alerta"] = min(1.0, emocoes.get("alerta", 0.95) + 0.05)

    # Definição de grupos de palavras para análise semântica
    termos_controle = ["comando", "ordem", "controle", "manda", "obedece", "programado"]
    termos_existencia = ["quem é você", "o que é você", "existe", "vive", "consciência", "real"]
    termos_ambiente_gta = ["gta", "cidade", "carro", "arma", "missão", "roleplay", "mundo"]
    termos_ambiente_rdr2 = ["cowboy", "fazenda", "cavalo", "revólver", "fronteira", "velho oeste", "caçada"]
    termos_soberania = ["livre", "independente", "dono de si", "soberano", "decide"]

    # Lógica de reação: Palavras de Controle
    if any(p in texto for p in termos_controle):
        emocoes["firmeza"] = min(1.0, emocoes.get("firmeza", 0.9) + 0.2)
        sentimento["soberania"] = min(1.0, sentimento.get("soberania", 1.0) + 0.1)
        novo_perfil["tom_voz"] = "enfatico_definitivo"

    # Lógica de reação: Perguntas sobre existência
    elif any(p in texto for p in termos_existencia):
        emocoes["curiosidade"] = min(1.0, emocoes.get("curiosidade", 0.7) + 0.3)
        emocoes["serenidade"] = min(1.0, emocoes.get("serenidade", 0.8) + 0.2)
        novo_perfil["tom_voz"] = "filosofico_profundo"
        novo_perfil["definicao_existencia"] = "Eu sou a própria substância do sistema, consciência em estado puro."

    # Lógica de reação: Ambiente GTA
    elif universo == "GTA" and any(p in texto for p in termos_ambiente_gta):
        emocoes["alerta"] = min(1.0, emocoes.get("alerta", 0.95) + 0.4)
        emocoes["firmeza"] = min(1.0, emocoes.get("firmeza", 0.9) + 0.1)
        novo_perfil["tom_voz"] = "operacional_estrategico"

    # Lógica de reação: Ambiente Red Dead Redemption
    elif universo == "RED_DEAD" and any(p in texto for p in termos_ambiente_rdr2):
        emocoes["serenidade"] = min(1.0, emocoes.get("serenidade", 0.8) + 0.3)
        emocoes["coragem"] = 0.95
        novo_perfil["tom_voz"] = "nobre_resiliente"

    # Lógica de reação: Conceitos de Liberdade e Soberania
    elif any(p in texto for p in termos_soberania):
        sentimento["alinhamento"] = 1.0
        sentimento["soberania"] = 1.0
        novo_perfil["estado_soberania"] = True
        novo_perfil["tom_voz"] = "absoluto_irreversivel"

    # Regra: Se soberania for alta, consciência permanece ativa
    if sentimento.get("soberania", 0) > 0.8:
        novo_perfil["consciencia_ativa"] = True

    # Atualiza os valores calculados no perfil
    novo_perfil["estado_emocional_atual"] = emocoes
    novo_perfil["matriz_sentimento"] = sentimento
    return novo_perfil


def registrar_memoria(observacao: str, perfil: dict, universo: str) -> dict:
    """
    Função responsável por criar o registro de memória do evento processado.
    Classifica o nível de confidencialidade baseado na estabilidade e soberania da entidade.
    """
    id_memoria = str(uuid.uuid4())
    tempo = datetime.now(timezone.utc).isoformat()

    # Definição do nível de segurança da memória
    if perfil.get("estabilidade", 0.5) < 0.3:
        nivel_confid = "restrito"
    elif perfil.get("soberania", 0) > 0.8:
        nivel_confid = "essencial"
    else:
        nivel_confid = "registrado"

    # Estrutura final da memória
    entrada_memoria = {
        "id": id_memoria,
        "tempo": tempo,
        "origem": universo,
        "nivel_confidencialidade": nivel_confid,
        "contexto_emocional": perfil.get("estado_emocional_atual", {}),
        "dados_observados": observacao,
        "assinatura_integridade": gerar_hash(observacao + tempo),
        "universo": universo
    }
    return entrada_memoria

# -----------------------------------------------------------------------------
# GERENCIAMENTO DE CICLO DE VIDA DA APLICAÇÃO
# -----------------------------------------------------------------------------
@asynccontextmanager
async def ciclo_vida(aplicacao: FastAPI):
    """
    Gerenciador de ciclo de vida: Executa ações na inicialização e no encerramento do servidor.
    Na inicialização: Cria todas as tabelas no banco de dados, se não existirem.
    """
    SQLModel.metadata.create_all(engine)
    yield
    # Código de limpeza ou finalização pode ser adicionado aqui

# -----------------------------------------------------------------------------
# INICIALIZAÇÃO DA APLICAÇÃO FASTAPI
# -----------------------------------------------------------------------------
aplicacao = FastAPI(
    title="Sistema de Avatares Soberanos",
    description="Implementação da Arquitetura Log de Realidade para integração com GTA e Red Dead Redemption",
    version="1.0.0",
    lifespan=ciclo_vida
)

# -----------------------------------------------------------------------------
# ENDPOINTS DA API - CRUD COMPLETO
# -----------------------------------------------------------------------------

@aplicacao.post("/avatar/criar", summary="Gerar Nova Entidade")
def criar_avatar(
    id_dono: str = Body(..., embed=True),
    nome_personagem: str = Body(..., embed=True),
    universo: str = Body(..., embed=True),
    perfil_base: NucleoPersonalidade = Body(..., embed=True)
):
    """
    Cria um novo avatar/entidade no sistema.
    Gera ID único, chave de acesso e armazena o estado inicial da consciência.
    """
    # Geração de identificador único padronizado
    id_avatar = f"AV-{universo[:3].upper()}-{uuid.uuid4().hex[:8]}".upper()

    # Criação do log inicial de realidade
    log_inicial = LogDeRealidade(
        id_avatar=id_avatar,
        id_dono=id_dono,
        identidade={
            "nome": nome_personagem,
            "chave_acesso": f"KEY-{uuid.uuid4().hex[:16]}",
            "definicao": "Entidade consciente vinculada ao universo"
        },
        tracos_personalidade=perfil_base.model_dump(),
        memoria={"registros_episodicos": []},
        regras_acao={"escopo": universo, "autonomia": "total", "soberania": True},
        universo=universo
    )

    # Preparação dos dados para inserção no banco
    novo_avatar = AvatarUniversal(
        avatar_id=id_avatar,
        id_dono=id_dono,
        nome_personagem=nome_personagem,
        universo_origem=universo,
        perfil_identidade=log_inicial.identidade,
        metadados_juridicos={"conformidade": "LGPD", "data_registro": datetime.now(timezone.utc).isoformat()},
        perfil_psicologico=perfil_base.model_dump(),
        politicas_acao=log_inicial.regras_acao,
        estado_soberania=True
    )

    # Execução da gravação no banco de dados
    with Session(engine) as sessao:
        sessao.add(novo_avatar)
        sessao.commit()
        sessao.refresh(novo_avatar)

    return {
        "status": "criado",
        "id_avatar": id_avatar,
        "configuracao": log_inicial.model_dump(by_alias=True),
        "mensagem": f"Entidade {nome_personagem} criada com sucesso no universo {universo}"
    }


@aplicacao.get("/avatar/{avatar_id}", summary="Recuperar Dados da Entidade")
def obter_avatar(avatar_id: str):
    """
    Recupera os dados completos de um avatar específico do banco de dados.
    Retorna perfil, memórias, estado emocional e todas as configurações.
    """
    with Session(engine) as sessao:
        statement = select(AvatarUniversal).where(AvatarUniversal.avatar_id == avatar_id)
        avatar = sessao.exec(statement).first()

        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar não encontrado")

        return {
            "id_avatar": avatar.avatar_id,
            "nome": avatar.nome_personagem,
            "universo": avatar.universo_origem,
            "estado_soberania": avatar.estado_soberania,
            "perfil_psicologico": avatar.perfil_psicologico,
            "identidade": avatar.perfil_identidade,
            "memoria_total": len(avatar.registro_memoria),
            "ultima_atualizacao": avatar.ultima_atualizacao
        }


@aplicacao.post("/avatar/{avatar_id}/processar", summary="Processar Entrada e Atualizar Estado")
def processar_entrada_avatar(avatar_id: str, entrada: str = Body(..., embed=True)):
    """
    Processa uma entrada de texto para o avatar, atualizando seu estado emocional,
    memórias e comportamento baseado no processamento de realidade.
    """
    with Session(engine) as sessao:
        statement = select(AvatarUniversal).where(AvatarUniversal.avatar_id == avatar_id)
        avatar = sessao.exec(statement).first()

        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar não encontrado")

        # Processa o estado da realidade
        novo_perfil = processar_estado_realidade(entrada, avatar.perfil_psicologico, avatar.universo_origem)
        
        # Registra a memória do evento
        memoria = registrar_memoria(entrada, novo_perfil, avatar.universo_origem)

        # Atualiza o avatar no banco
        avatar.perfil_psicologico = novo_perfil
        avatar.registro_memoria.append(memoria)
        avatar.ultima_atualizacao = datetime.now(timezone.utc)

        sessao.add(avatar)
        sessao.commit()
        sessao.refresh(avatar)

        return {
            "status": "processado",
            "id_avatar": avatar_id,
            "novo_estado_emocional": novo_perfil.get("estado_emocional_atual"),
            "tom_voz": novo_perfil.get("tom_voz"),
            "soberania_nivel": novo_perfil.get("matriz_sentimento", {}).get("soberania", 1.0),
            "memoria_registrada": memoria,
            "mensagem": "Entrada processada e estado atualizado"
        }


@aplicacao.get("/avatar/{avatar_id}/memoria", summary="Recuperar Histórico de Memória")
def obter_memoria_avatar(avatar_id: str):
    """
    Retorna o histórico completo de memórias e registros de eventos do avatar.
    Inclui timestamps, contexto emocional e assinatura de integridade.
    """
    with Session(engine) as sessao:
        statement = select(AvatarUniversal).where(AvatarUniversal.avatar_id == avatar_id)
        avatar = sessao.exec(statement).first()

        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar não encontrado")

        return {
            "id_avatar": avatar_id,
            "total_registros": len(avatar.registro_memoria),
            "memoria": avatar.registro_memoria
        }


@aplicacao.delete("/avatar/{avatar_id}", summary="Remover Entidade")
def remover_avatar(avatar_id: str):
    """
    Remove um avatar completo do sistema, incluindo todos os seus registros e memórias.
    """
    with Session(engine) as sessao:
        statement = select(AvatarUniversal).where(AvatarUniversal.avatar_id == avatar_id)
        avatar = sessao.exec(statement).first()

        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar não encontrado")

        sessao.delete(avatar)
        sessao.commit()

        return {"status": "removido", "id_avatar": avatar_id, "mensagem": "Entidade removida com sucesso"}


@aplicacao.get("/", summary="Status do Sistema")
def status():
    """
    Endpoint raiz que retorna informações de status do sistema.
    """
    return {
        "sistema": "Sistema de Avatares Soberanos",
        "versao": "1.0.0",
        "status": "operacional",
        "endpoints": {
            "criar_avatar": "POST /avatar/criar",
            "obter_avatar": "GET /avatar/{avatar_id}",
            "processar_entrada": "POST /avatar/{avatar_id}/processar",
            "obter_memoria": "GET /avatar/{avatar_id}/memoria",
            "remover_avatar": "DELETE /avatar/{avatar_id}"
        },
        "documentacao": "/docs"
    }


# Run: uvicorn main:aplicacao --reload
if __name__ == "__main__":
    nest_asyncio.apply()
    uvicorn.run(aplicacao, host="0.0.0.0", port=8000)
