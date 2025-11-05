from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Browser, Page
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base Scraper Class"""
    
    def __init__(self, site_name: str, headless: bool = True):
        self.site_name = site_name
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_url: str = ""
        
    @abstractmethod
    def get_base_url(self) -> str:
        """get the base URL of the site"""
        pass
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        authentication method - subclasses implement specific login logic
        
        Args: 
            credentials (Dict[str, str]): login credentials
        Returns: 
            bool: whether authentication was successful
        """
        pass
    
    @abstractmethod
    async def extract_data(self, page_url: str) -> List[Dict[str, Any]]:
        """
        extract data from a given page URL
        Args:
            page_url (str): the URL of the page to extract data from
        Returns:
            List[Dict[str, Any]]: the extracted data
        """
        pass
    
    async def init_browser(self):
        """init the btrowser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        logger.info(f"[{self.site_name}] completed browser initialization")
    
    async def close_browser(self):
        """close the browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        logger.info(f"[{self.site_name}] the browser has been closed")
    
    async def navigate_to(self, url: str, wait_time: int = 3000):
        """navigate to a URL"""
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await self.page.wait_for_timeout(wait_time)
            logger.info(f"[{self.site_name}] successfully navigated to: {url}")
        except Exception as e:
            logger.error(f"[{self.site_name}] failed to navigate to: {str(e)}")
            raise
    
    async def run(self, credentials: Optional[Dict[str, str]] = None, 
                  urls: List[str] = None) -> List[Dict[str, Any]]:
        """main method to run the scraper"""
        try:
            await self.init_browser()
            
            # authenticate
            if credentials:
                auth_success = await self.authenticate(credentials)
                if not auth_success:
                    logger.error(f"[{self.site_name}] authentication failed")
                    return []
            
            # extract data
            all_data = []
            if urls:
                for url in urls:
                    data = await self.extract_data(url)
                    all_data.extend(data)
            
            return all_data
        
        except Exception as e:
            logger.error(f"[{self.site_name}] execution failed: {str(e)}")
            raise
        
        finally:
            await self.close_browser()
