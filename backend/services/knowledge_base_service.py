"""Knowledge Base Service - handles multi-source KB queries"""

import logging
from typing import List, Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing knowledge base across multiple sources"""
    
    def __init__(self):
        self.strapi_url = settings.strapi_url
        self.strapi_token = settings.strapi_api_token
        self.qa_db_url = settings.qa_database_url
        
    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[dict]:
        """
        Search knowledge base across all sources.
        
        Priority order:
        1. Strapi CMS
        2. Q&A Dataset
        3. GPT (fallback)
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum results to return
            
        Returns:
            List of results with source information
        """
        results = []
        
        try:
            # Search Strapi
            strapi_results = await self._search_strapi(query, category, limit)
            results.extend(strapi_results)
            
            # Search Q&A Database
            qa_results = await self._search_qa_db(query, category, limit - len(results))
            results.extend(qa_results)
            
            # If no results, use GPT as fallback
            if not results:
                gpt_results = await self._search_gpt_fallback(query, category, limit)
                results.extend(gpt_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            raise
    
    async def _search_strapi(
        self,
        query: str,
        category: Optional[str],
        limit: int
    ) -> List[dict]:
        """Search Strapi CMS"""
        try:
            # Implementation pending - requires Strapi API integration
            logger.info(f"Searching Strapi for: {query}")
            return []
        except Exception as e:
            logger.error(f"Error searching Strapi: {str(e)}")
            return []
    
    async def _search_qa_db(
        self,
        query: str,
        category: Optional[str],
        limit: int
    ) -> List[dict]:
        """Search Q&A Database"""
        try:
            # Implementation pending - requires Q&A database integration
            logger.info(f"Searching Q&A DB for: {query}")
            return []
        except Exception as e:
            logger.error(f"Error searching Q&A DB: {str(e)}")
            return []
    
    async def _search_gpt_fallback(
        self,
        query: str,
        category: Optional[str],
        limit: int
    ) -> List[dict]:
        """Use GPT as fallback when KB search returns no results"""
        try:
            # Implementation pending - requires GPT API call
            logger.info(f"Using GPT fallback for: {query}")
            return [{
                "question": query,
                "answer": "GPT fallback response - implementation pending",
                "source": "gpt",
                "confidence": 0.0
            }]
        except Exception as e:
            logger.error(f"Error in GPT fallback: {str(e)}")
            return []
    
    async def get_categories(self) -> List[str]:
        """Get available knowledge base categories"""
        return ["general", "medical", "faq", "temi_features", "troubleshooting"]
    
    async def reindex(self) -> dict:
        """Reindex all knowledge base sources"""
        try:
            logger.info("Starting knowledge base reindex")
            return {
                "status": "reindexing",
                "timestamp": "pending"
            }
        except Exception as e:
            logger.error(f"Error reindexing KB: {str(e)}")
            raise


# Global KB service instance
kb_service = KnowledgeBaseService()
