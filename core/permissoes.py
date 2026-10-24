"""Autorização: nível do usuário x nível mínimo do recurso (APS-17)."""
import config


def exige_segundo_fator(recurso: dict) -> bool:
    """Cofre de nível 3: prova de vida + PIN além do rosto."""
    return recurso["nivel_minimo"] >= 3


def autorizar(usuario: dict, recurso: dict, agora):
    """Retorna (concedido, motivo). `motivo` é um valor do ENUM acessos.resultado."""
    if not usuario or not usuario["ativo"]:
        return False, "nao_reconhecido"
    if usuario["nivel"] < recurso["nivel_minimo"]:
        return False, "negado_nivel"
    if (recurso["divisao_id"] and usuario["nivel"] == 2
            and usuario["divisao_id"] != recurso["divisao_id"]):
        return False, "negado_divisao"
    inicio, fim = config.HORARIO_EXPEDIENTE
    if usuario["nivel"] == 2 and not (inicio <= agora.hour < fim):
        return False, "negado_horario"
    return True, "concedido"
