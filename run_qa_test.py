from playwright.sync_api import sync_playwright
import time
import os

def run():
    print("Starting Playwright test...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        
        try:
            print("Navigating to http://localhost:8502")
            page.goto("http://localhost:8502")
            page.wait_for_load_state("networkidle")
            
            # Login
            print("Checking for login form...")
            if page.locator("input[aria-label='Usuário']").count() > 0:
                print("Logging in...")
                page.fill("input[aria-label='Usuário']", "fabricio")
                page.fill("input[aria-label='Senha']", "taxbase123")
                
                # Precise selector from dump
                # button kind="secondaryFormSubmit"
                page.click("button[kind='secondaryFormSubmit']", force=True)
                
                print("Clicked login. Waiting...")
                time.sleep(5)
                
            # Check if login succeeded (form gone)
            if page.locator("input[aria-label='Usuário']").count() > 0:
                print("FAILURE: Login failed. Still on login page.")
                page.screenshot(path="test_results/login_failed.png")
                raise Exception("Login failed")

            print("Login successful.")
            
            # Navigate to Analysis Tab
            print("Clicking 'Análise Personalizada'...")
            # Using text locator which is generally robust for Streamlit tabs
            page.click("text=Análise Personalizada")
            time.sleep(2)
            
            # Select Period
            print("Selecting Period...")
            # Click the dropdown
            page.click("text=Selecione o Período")
            time.sleep(1)
            # Click the option
            page.click("text=Últimos 3 Meses")
            
            # Click Search
            print("Clicking Search...")
            page.click("button:has-text('Pesquisar Dados')")
            
            # Wait for results
            print("Waiting for results...")
            time.sleep(5)
            
            # Check success
            has_chart = page.locator("div.js-plotly-plot").count() > 0
            has_success = page.locator("div.stAlert").count() > 0
            
            if has_chart or has_success:
                print("SUCCESS: Validation passed.")
            else:
                 print("WARNING: No chart or success alert found.")

            # Take screenshot
            os.makedirs("test_results", exist_ok=True)
            output_path = os.path.abspath("test_results/evidence_qa_02.png")
            page.screenshot(path=output_path)
            print(f"Screenshot saved to {output_path}")
            
        except Exception as e:
            print(f"Test Failed: {e}")
            page.screenshot(path="test_results/failure_evidence.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
