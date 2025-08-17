"""
Historical Knowledge AI
Provides historical context for Western-themed stories
"""

from typing import Optional
from anthropic import AsyncAnthropic

class HistoricalKnowledgeAI:
    """IA pour les connaissances historiques du Western"""
    
    def __init__(self, api_key: str, model_name: str = "claude-3-haiku-20240307"):
        """Initialise l'IA avec la clé API Anthropic"""
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model_name
        self.is_enabled = False
        
    def enable(self):
        """Active les informations historiques"""
        self.is_enabled = True
        print("🤖 Informations historiques activées")
    
    def disable(self):
        """Désactive les informations historiques"""
        self.is_enabled = False
        print("🤖 Informations historiques désactivées")
    
    async def get_historical_context(self, text: str) -> Optional[str]:
        """Génère des informations historiques pour le texte donné"""
        if not self.is_enabled:
            return None
            
        try:
            # Construire le prompt
            prompt = (
                "Tu es un expert en histoire du Western américain. "
                "Analyse ce texte et fournis 2-3 phrases d'informations historiques pertinentes. "
                "Réponds en français, de manière éducative mais accessible. "
                "Concentre-toi sur les éléments historiques comme les armes, lieux, personnages ou la culture de l'époque.\n\n"
                f"Texte à analyser:\n{text}\n\n"
                "Informations historiques:"
            )
            
            # Appeler l'API Anthropic
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=150,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return message.content[0].text if message.content else None
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération du contexte historique: {e}")
            return None