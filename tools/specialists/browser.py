"""
🌐 BROWSER AGENT
================
Contrôle du navigateur avec Playwright

Permet:
- Ouvrir Chrome
- Cliquer
- Remplir formulaires
- Tester des sites
- Scraper données
"""

from __future__ import annotations

import json
from pathlib import Path

# Note: Playwright doit être installé (pip install playwright && playwright install chromium)


class BrowserAgent:
    """
    Agent de contrôle du navigateur via Playwright
    
    Fonctionnalités:
    - Navigation
    - Interactions (clic, remplissage)
    - Screenshots
    - Scrapping
    - Tests automatisés
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None
        self._playwright = None
        
    async def _ensure_browser(self):
        """Démarre le navigateur si pas déjà fait."""
        if self.browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = async_playwright()
                await self._playwright.start()
                self.browser = await self._playwright.chromium.launch(
                    headless=self.headless
                )
                self.page = await self.browser.new_page()
            except ImportError:
                return False
        return True
    
    async def open(self, url: str) -> dict:
        """Ouvre une URL."""
        if not await self._ensure_browser():
            return {"error": "Playwright non installé: pip install playwright"}
        
        try:
            await self.page.goto(url, wait_until="networkidle")
            title = await self.page.title()
            return {
                "ok": True,
                "url": url,
                "title": title
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def click(self, selector: str) -> dict:
        """Clique sur un élément CSS."""
        if not self.page:
            return {"error": "Navigateur non initialisé"}
        
        try:
            await self.page.click(selector)
            return {"ok": True, "selector": selector}
        except Exception as e:
            return {"error": str(e)}
    
    async def fill(self, selector: str, value: str) -> dict:
        """Remplit un champ."""
        if not self.page:
            return {"error": "Navigateur non initialisé"}
        
        try:
            await self.page.fill(selector, value)
            return {"ok": True, "selector": selector, "value": value}
        except Exception as e:
            return {"error": str(e)}
    
    async def type_text(self, selector: str, text: str, delay: int = 100) -> dict:
        """Tape du texte avec délai."""
        if not self.page:
            return {"error": "Navigateur non initialisé"}
        
        try:
            await self.page.type(selector, text, delay=delay)
            return {"ok": True, "selector": selector, "text": text}
        except Exception as e:
            return {"error": str(e)}
    
    async def wait_for(self, selector: str, timeout: int = 30000) -> dict:
        """Attend un élément."""
        if not self.page:
            return {"error": "Navigateur non initialisé"}
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {"ok": True, "selector": selector}
        except Exception as e:
            return {"error": str(e)}
    
    async def screenshot(self, path: str = "screenshot.png", full_page: bool = False) -> dict:
        """Prend une capture d'écran."""
        if not self.page:
            return {"error": "Navigateur non initialisé"}
        
        try:
            await self.page.screenshot(path=path, full_page=full_page)
            return {"ok": True, "path": path}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_text(self, selector: str) -> dict:
        """Récupère le texte d'un élément."""
        if not self.page:
            return {"error": "Navigateur non initialisé"}
        
        try:
            text = await self.page.text_content(selector)
            return {"ok": True, "selector": selector, "text": text}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_html(self) -> dict:
        """Récupère le HTML de la page."""
        if not self.page:
            return {"error": "Navigateur non initialisé"}
        
        try:
            html = await self.page.content()
            return {"ok": True, "html": html[:50000]}  # Limite taille
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_script(self, script: str) -> dict:
        """Exécute du JavaScript."""
        if not self.page:
            return {"error": "Navigateur non initialisé"}
        
        try:
            result = await self.page.evaluate(script)
            return {"ok": True, "result": result}
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """Ferme le navigateur."""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        self.browser = None
        self.page = None
    
    # ========== CONVENIENCE METHODS ==========
    
    async def test_login(self, url: str, username: str, password: str,
                        username_selector: str = "#username",
                        password_selector: str = "#password",
                        submit_selector: str = "button[type='submit']") -> dict:
        """Teste un formulaire de login."""
        result = await self.open(url)
        if "error" in result:
            return result
        
        # Remplir username
        await self.fill(username_selector, username)
        
        # Remplir password
        await self.fill(password_selector, password)
        
        # Cliquer sur submit
        await self.click(submit_selector)
        
        # Attendre un peu
        await self.page.wait_for_timeout(2000)
        
        # Vérifier si login OK (détection simple)
        current_url = self.page.url
        return {
            "ok": True,
            "tested": True,
            "final_url": current_url,
            "success": "login" in current_url.lower() or "dashboard" in current_url.lower()
        }
    
    async def scrape_table(self, table_selector: str = "table") -> dict:
        """Scrape un tableau HTML."""
        if not self.page:
            return {"error": "Navigateur non initialisé"}
        
        try:
            rows = await self.page.query_selector_all(f"{table_selector} tr")
            data = []
            for row in rows:
                cells = await row.query_selector_all("td, th")
                row_data = [await cell.text_content() for cell in cells]
                if row_data:
                    data.append(row_data)
            return {"ok": True, "data": data}
        except Exception as e:
            return {"error": str(e)}


# ========== SYNC VERSION (pour usage simple) ==========

class SimpleBrowser:
    """Version synchrone simplifiée pour usage direct."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        
    def open(self, url: str) -> str:
        """Ouvre une URL (synchrone)."""
        import asyncio
        agent = BrowserAgent(self.headless)
        
        async def run():
            return await agent.open(url)
        
        result = asyncio.run(run())
        return json.dumps(result)
    
    def screenshot(self, path: str = "screenshot.png") -> str:
        """Prend un screenshot."""
        import asyncio
        agent = BrowserAgent(self.headless)
        
        async def run():
            await agent.open("about:blank")  # Initialize
            return await agent.screenshot(path)
        
        result = asyncio.run(run())
        return json.dumps(result)


# Installation:
# pip install playwright
# playwright install chromium
#
# Usage:
# browser = BrowserAgent(headless=False)
# result = asyncio.run(browser.open("https://google.com"))
# asyncio.run(browser.screenshot("google.png"))
# asyncio.run(browser.close())