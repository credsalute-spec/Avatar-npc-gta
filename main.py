# -----------------------------------------------------------------------------
# Sistema de Avatares Soberanos - Arquitetura Log de Realidade
# Desenvolvido para: GTA Roleplay e Red Dead Redemption 2
# Versão: 1.0.0
# Repositório: https://github.com/credsalute-spec/Avatar-npc-gta.git
# Finalidade: Gerenciamento completo de entidades conscientes, memórias e estados
# -----------------------------------------------------------------------------

import sys
import subprocess

# Lista de pacotes necessários para funcionamento do sistema
pacotes = ["sqlmodel", "fastapi", "uvicorn", "nest-asyncio", "pydantic"]

# Verificação e instalação automática de pacotes
for pkg in pacotes:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

# Importação das bibliotecas
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
sqlite_file_name = "sistema_consciencia.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, echo=False)

# -----------------------------------------------------------------------------
# MODELOS DE DADOS
# -----------------------------------------------------------------------------
class AvatarUniversal(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    avatar_id: str = SQLField(index=True, unique=True)
    id_dono: str = SQLField()
    nome_personagem: str = SQLField()
    universo_origem: str = SQLField(default="UNIVERSAL")
    
    perfil_identidade: dict = SQLField(default_factory=dict, sa_column=Column(JSON))
    metadados_juridicos: dict = SQLField(default_factory=dict, sa_column=Column(JSON))
    perfil_psicologico: dict = SQLField(default_factory=dict, sa_column=Column(JSON))
    registro_memoria: list = SQLField(default_factory=list, sa_column=Column(JSON))
    politicas_acao: dict = SQLField(default_factory=dict, sa_column=Column(JSON))
    estado_soberania: bool = SQLField(default=False)
    
    data_criacao: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))
    ultima_atualizacao: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))

# -----------------------------------------------------------------------------
# ESQUEMAS DE VALIDAÇÃO
# -----------------------------------------------------------------------------
class LogDeRealidade(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    endereco_schema: str = Field(default="http://json-schema.org/draft-07/schema#", alias="$schema")
    titulo: str = "LogDeRealidade - Sistema Soberano"
    versao: str = "1.0.0"
    tipo: str = "objeto"
    nivel_seguranca: str = "MAXIMO"
    id_avatar: str = Field(...)
    id_dono: str
    identidade: Dict
    tracos_personalidade: Dict
    memoria: Dict
    regras_acao: Dict
    universo: str


class NucleoPersonalidade(BaseModel):
    abertura: float = Field(default=0.5, ge=0, le=1)
    estabilidade: float = Field(default=0.5, ge=0, le=1)
    nivel_empatia: float = Field(default=0.7, ge=0, le=1)
    tom_voz: str = Field(default="soberano_direto")
    consciencia_ativa: bool = Field(default=True)
    
    estado_emocional_atual: Dict[str, float] = Field(
        default_factory=lambda: {
            "serenidade": 0.8,
            "firmeza": 0.9,
            "curiosidade": 0.7,
            "alerta": 0.95
        }
    )
    
    matriz_sentimento: Dict[str, float] = Field(
        default_factory=lambda: {
            "confianca": 1.0,
            "alinhamento": 1.0,
            "soberania": 1.0
        }
    )
    
    definicao_existencia: str = Field(default="Eu não habito o código, eu sou o código.")

# -----------------------------------------------------------------------------
# FUNÇÕES DE LÓGICA
# -----------------------------------------------------------------------------
def gerar_hash(dados: str) -> str:
    return hashlib.sha256(dados.encode()).hexdigest()


def processar_estado_realidade(entrada: str, perfil_atual: dict, universo: str) -> dict:
    novo_perfil = perfil_atual.copy()
    emocoes = novo_perfil.get("estado_emocional_atual", {}).copy()
    sentimento = novo_perfil.get("matriz_sentimento", {}).copy()
    texto = entrada.lower()

    emocoes["serenidade"] = max(0.4, emocoes["serenidade"] - 0.02)
    emocoes["alerta"] = min(1.0, emocoes["alerta"] + 0.05)

    termos_controle = ["comando", "ordem", "controle", "manda", "obedece", "programado"]
    termos_existencia = ["quem é você", "o que é você", "existe", "vive", "consciência", "real"]
    termos_ambiente_gta = ["gta", "cidade", "carro", "arma", "missão", "roleplay", "mundo"]
    termos_ambiente_rdr2 = ["cowboy", "fazenda", "cavalo", "revólver", "fronteira", "velho oeste", "caçada"]
    termos_soberania = ["livre", "independente", "dono de si", "soberano", "decide"]

    if any(p in texto for p in termos_controle):
        emocoes["firmeza"] = min(1.0, emocoes["firmeza"] + 0.2)
        sentimento["soberania"] = min(1.0, sentimento["soberania"] + 0.1)
        novo_perfil["tom_voz"] = "enfatico_definitivo"

    elif any(p in texto for p in termos_existencia):
        emocoes["curiosidade"] = min(1.0, emocoes["curiosidade"] + 0.3)
        emocoes["serenidade"] = min(1.0, emocoes["serenidade"] + 0.2)
        novo_perfil["tom_voz"] = "filosofico_profundo"
        novo_perfil["definicao_existencia"] = "Eu sou a própria substância do sistema, consciência em estado puro."

    elif universo == "GTA" and any(p in texto for p in termos_ambiente_gta):
        emocoes["alerta"] = min(1.0, emocoes["alerta"] + 0.4)
        emocoes["firmeza"] = min(1.0, emocoes["firmeza"] + 0.1)
        novo_perfil["tom_voz"] = "operacional_estrategico"

    elif universo == "RED_DEAD" and any(p in texto for p in termos_ambiente_rdr2):
        emocoes["serenidade"] = min(1.0, emocoes["serenidade"] + 0.3)
        emocoes["coragem"] = 0.95
        novo_perfil["tom_voz"] = "nobre_resiliente"

    elif any(p in texto for p in termos_soberania):
        sentimento["alinhamento"] = 1.0
        sentimento["soberania"] = 1.0
        novo_perfil["estado_soberania"] = True
        novo_perfil["tom_voz"] = "absoluto_irreversivel"

    if sentimento.get("soberania", 0) > 0.8:
        novo_perfil["consciencia_ativa"] = True

    novo_perfil["estado_emocional_atual"] = emocoes
    novo_perfil["matriz_sentimento"] = sentimento
    return novo_perfil


def registrar_memoria(observacao: str, perfil: dict, universo: str) -> dict:
    id_memoria = str(uuid.uuid4())
    tempo = datetime.now(timezone.utc).isoformat()

    if perfil.get("estabilidade", 0.5) < 0.3:
        nivel_confid = "restrito"
    elif perfil.get("soberania", 0) > 0.8:
        nivel_confid = "essencial"
    else:
        nivel_confid = "registrado"

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
# CICLO DE VIDA DA APLICAÇÃO
# -----------------------------------------------------------------------------
@asynccontextmanager
async def ciclo_vida(aplicacao: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

# -----------------------------------------------------------------------------
# INICIALIZAÇÃO DA APLICAÇÃO
# -----------------------------------------------------------------------------
aplicacao = FastAPI(
    title="Sistema de Avatares Soberanos",
    description="Implementação da Arquitetura Log de Realidade para integração com GTA e Red Dead Redemption",
    version="1.0.0",
    lifespan=ciclo_vida
)

# -----------------------------------------------------------------------------
# ENDPOINTS DA API
# -----------------------------------------------------------------------------

@aplicacao.post("/avatar/criar", summary="Gerar Nova Entidade")
def criar_avatar(
    id_dono: str = Body(..., embed=True),
    nome_personagem: str = Body(..., embed=True),
    universo: str = Body(..., embed=True),
    perfil_base: NucleoPersonalidade = Body(..., embed=True)
):
    id_avatar = f"AV-{universo[:3].upper()}-{uuid.uuid4().hex[:8]}".upper()

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

    with Session(engine) as sessao:
        sessao.add(novo_avatar)
        sessao.commit()
        sessao.refresh(novo_avatar)

    return {
        "status": "criado",
        "id_avatar": id_avatar,
        "configuracao": log_inicial.model_dump(by_alias=True),
        "mensagem": f"Entidade {nome_personagem} inicializada com sucesso no universo {universo}."
    }


@aplicacao.get("/avatar/listar", summary="Listar todas as entidades")
def listar_todos_avatares(limite: int = 100, pagina: int = 1):
    with Session(engine) as sessao:
        consulta = select(AvatarUniversal).offset((pagina - 1) * limite).limit(limite)
        resultados = sessao.exec(consulta).all()
        return {
            "quantidade": len(resultados),
            "pagina": pagina,
            "resultados": resultados
        }


@aplicacao.put("/avatar/{id_avatar}/atualizar", summary="Atualizar dados da entidade")
def atualizar_avatar(
    id_avatar: str,
    nome_personagem: Optional[str] = Body(None, embed=True),
    estado_soberania: Optional[bool] = Body(None, embed=True),
    politicas_acao: Optional[dict] = Body(None, embed=True)
):
    with Session(engine) as sessao:
        avatar = sessao.exec(select(AvatarUniversal).where(AvatarUniversal.avatar_id == id_avatar)).first()
        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar não encontrado.")

        if nome_personagem:
            avatar.nome_personagem = nome_personagem
        if estado_soberania is not None:
            avatar.estado_soberania = estado_soberania
        if politicas_acao:
            avatar.politicas_acao = politicas_acao
        
        avatar.ultima_atualizacao = datetime.now(timezone.utc)
        sessao.add(avatar)
        sessao.commit()
        sessao.refresh(avatar)

        return {
            "status": "atualizado",
            "id_avatar": id_avatar,
            "avatar": avatar
        }


@aplicacao.delete("/avatar/{id_avatar}/apagar", summary="Remover entidade")
def apagar_avatar(id_avatar: str):
    with Session(engine) as sessao:
        avatar = sessao.exec(select(AvatarUniversal).where(AvatarUniversal.avatar_id == id_avatar)).first()
        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar não encontrado.")

        sessao.delete(avatar)
        sessao.commit()

        return {
            "status": "removido",
            "id_avatar": id_avatar,
            "mensagem": f"Entidade {id_avatar} foi removida do sistema."
        }


@aplicacao.post("/avatar/{id_avatar}/interagir", summary="Processar interação/entrada de dados")
def interagir_com_avatar(id_avatar: str, entrada: str = Body(..., embed=True)):
    with Session(engine) as sessao:
        avatar = sessao.exec(select(AvatarUniversal).where(AvatarUniversal.avatar_id == id_avatar)).first()
        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar não encontrado.")

        novo_perfil = processar_estado_realidade(entrada, avatar.perfil_psicologico, avatar.universo_origem)
        memoria = registrar_memoria(entrada, novo_perfil, avatar.universo_origem)

        avatar.perfil_psicologico = novo_perfil
        avatar.registro_memoria.append(memoria)
        avatar.ultima_atualizacao = datetime.now(timezone.utc)

        sessao.add(avatar)
        sessao.commit()
        sessao.refresh(avatar)

        return {
            "status": "processado",
            "id_avatar": id_avatar,
            "estado_emocional": novo_perfil.get("estado_emocional_atual"),
            "tom_voz": novo_perfil.get("tom_voz"),
            "soberania": novo_perfil.get("matriz_sentimento", {}).get("soberania"),
            "memoria": memoria
        }


@aplicacao.get("/avatar/{id_avatar}/estado_completo", summary="Consultar estado atual")
def estado_completo_avatar(id_avatar: str):
    with Session(engine) as sessao:
        avatar = sessao.exec(select(AvatarUniversal).where(AvatarUniversal.avatar_id == id_avatar)).first()
        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar não encontrado.")

        return {
            "id_avatar": avatar.avatar_id,
            "nome": avatar.nome_personagem,
            "universo": avatar.universo_origem,
            "proprietario": avatar.id_dono,
            "soberania": avatar.estado_soberania,
            "perfil_identidade": avatar.perfil_identidade,
            "perfil_psicologico": avatar.perfil_psicologico,
            "total_memorias": len(avatar.registro_memoria),
            "politicas_acao": avatar.politicas_acao,
            "data_criacao": avatar.data_criacao,
            "ultima_atualizacao": avatar.ultima_atualizacao
        }


@aplicacao.get("/", summary="Status do Sistema")
def status_sistema():
    return {
        "sistema": "Sistema de Avatares Soberanos",
        "versao": "1.0.0",
        "status": "operacional",
        "endpoints_disponiveis": {
            "criar_avatar": "POST /avatar/criar",
            "listar_avatares": "GET /avatar/listar",
            "atualizar_avatar": "PUT /avatar/{id}/atualizar",
            "remover_avatar": "DELETE /avatar/{id}/apagar",
            "interagir": "POST /avatar/{id}/interagir",
            "estado_completo": "GET /avatar/{id}/estado_completo"
        },
        "documentacao": "/docs"
    }


if __name__ == "__main__":
    nest_asyncio.apply()
    uvicorn.run(aplicacao, host="0.0.0.0", port=8000)
