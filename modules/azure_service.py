# modules/azure_service.py
"""
Servicio de Azure OpenAI con soporte para Function Calling y Retries.
Versión Blindada: Maneja deployments por defecto para evitar errores de argumentos.
"""

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential
import streamlit as st

class AzureBotClient:
    def __init__(self, endpoint, api_key, deployment="gpt-4-1-preview", api_version="2024-05-01-preview"):
        """
        Inicializa el cliente de Azure OpenAI.
        
        Args:
            endpoint (str): URL del recurso.
            api_key (str): Clave de API.
            deployment (str, optional): Nombre del modelo desplegado. Defaults to "gpt-4-1-preview".
            api_version (str, optional): Versión de la API. Defaults to "2024-05-01-preview".
        """
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        self.deployment = deployment

    # Decorador de robustez: Reintenta hasta 3 veces si falla la conexión
    @retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(3))
    def chat_completion(self, messages, tools=None, tool_choice="auto", temperature=0.3):
        """
        Envía mensajes a Azure GPT-4 soportando herramientas nativas.
        """
        try:
            # Validar si se pasaron herramientas
            if tools:
                return self.client.chat.completions.create(
                    model=self.deployment,
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    temperature=temperature
                )
            else:
                return self.client.chat.completions.create(
                    model=self.deployment,
                    messages=messages,
                    temperature=temperature
                )
        except Exception as e:
            # Si falla, lanzamos el error para que tenacity intente de nuevo o lo capturemos fuera
            raise e