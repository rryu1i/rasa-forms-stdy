from typing import Any, Text, Dict, List, Optional

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
import re # Para limpeza opcional

# Definir os valores canônicos esperados para tipo_exame (minúsculo)
TIPO_EXAME_TC_TORAX = "tomografia computadorizada do torax"
TIPO_EXAME_RM_NEURO = "ressonancia magnetica neuro"
TIPOS_EXAME_VALIDOS = [TIPO_EXAME_TC_TORAX, TIPO_EXAME_RM_NEURO]

class ValidateAnamneseForm(FormValidationAction):
    """Action de validação para o anamnese_form."""

    def name(self) -> Text:
        # Nome da action deve corresponder ao listado no domain.yml
        return "validate_anamnese_form"

    async def required_slots(
        self,
        slots_map: Dict[Text, Any],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Optional[List[Text]]:
        """Define dinamicamente os slots necessários com base no tipo de exame."""

        # Slots sempre necessários no início
        # Usamos a ordem que você definiu nas formas originais como guia
        required = ["nome_paciente", "tipo_exame"]

        # Pega o valor já validado (ou não) do slot tipo_exame
        tipo_exame = tracker.get_slot("tipo_exame")

        if tipo_exame:
            tipo_exame_lower = str(tipo_exame).lower() # Garante minúsculas

            # Adiciona slots comuns a ambos os caminhos, se houver
            # Baseado nos seus forms originais, motivo e tempo são comuns
            required.extend(["motivo_exame", "tempo_sintomas"])

            # Adiciona slots condicionais
            if tipo_exame_lower == TIPO_EXAME_TC_TORAX:
                required.append("historico_de_trauma")
            elif tipo_exame_lower == TIPO_EXAME_RM_NEURO:
                required.append("historico_de_cirurgia") # Corrigido nome do slot

        # Retorna a lista completa de slots requeridos ATÉ O MOMENTO
        # O Rasa pedirá o próximo slot não preenchido da lista
        # print(f"Required slots calculated: {required}") # Debug
        return required

    def validate_nome_paciente(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida o nome do paciente."""
        if isinstance(slot_value, str) and len(slot_value.strip()) > 2:
            nome_limpo = re.sub(r'\s+', ' ', slot_value).strip().title()
            return {"nome_paciente": nome_limpo}
        else:
            dispatcher.utter_message(response="utter_ask_nome_paciente") # Pede novamente
            return {"nome_paciente": None}

    def validate_tipo_exame(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida o tipo de exame e retorna o valor canônico."""
        if isinstance(slot_value, str):
            # Tenta mapear variações comuns (simplificado)
            # Idealmente, usar entities com sinônimos ou lookup tables
            valor_lower = slot_value.lower()
            if "tomografia" in valor_lower and ("torax" in valor_lower or "peito" in valor_lower):
                 valor_canonico = TIPO_EXAME_TC_TORAX
            elif ("ressonancia" in valor_lower or "rm" in valor_lower) and ("neuro" in valor_lower or "cabeça" in valor_lower or "cranio" in valor_lower):
                 valor_canonico = TIPO_EXAME_RM_NEURO
            else:
                 valor_canonico = None # Não reconhecido

            if valor_canonico in TIPOS_EXAME_VALIDOS:
                 print(f"Valid tipo_exame found: {valor_canonico}") # Debug
                 return {"tipo_exame": valor_canonico}

        # Se não validou, pede novamente
        dispatcher.utter_message(response="utter_ask_tipo_exame")
        return {"tipo_exame": None}

    def validate_motivo_exame(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida o motivo do exame (simplesmente verifica se não está vazio)."""
        if isinstance(slot_value, str) and slot_value.strip():
            return {"motivo_exame": slot_value.strip()}
        else:
            dispatcher.utter_message(response="utter_ask_motivo_exame")
            return {"motivo_exame": None}

    def validate_tempo_sintomas(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida o tempo dos sintomas (verifica se não está vazio)."""
        if isinstance(slot_value, str) and slot_value.strip():
            return {"tempo_sintomas": slot_value.strip()}
        else:
            dispatcher.utter_message(response="utter_ask_tempo_sintomas")
            return {"tempo_sintomas": None}

    # Validações booleanas (verificam se o mapeamento from_intent funcionou)
    def validate_historico_de_trauma(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        """Valida a resposta booleana."""
        if isinstance(slot_value, bool):
            return {"historico_de_trauma": slot_value}
        dispatcher.utter_message(text="Por favor, responda com 'sim' ou 'não'.") # Fallback message
        dispatcher.utter_message(response="utter_ask_historico_de_trauma") # Repete a pergunta original
        return {"historico_de_trauma": None}

    def validate_historico_de_cirurgia( # Nome da função corrigido
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        """Valida a resposta booleana."""
        if isinstance(slot_value, bool):
            return {"historico_de_cirurgia": slot_value}
        dispatcher.utter_message(text="Por favor, responda com 'sim' ou 'não'.")
        dispatcher.utter_message(response="utter_ask_historico_de_cirurgia") # Repete a pergunta original
        return {"historico_de_cirurgia": None}