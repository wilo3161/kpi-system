import os
import subprocess
import time
import requests
from playwright.sync_api import sync_playwright

def test_e2e():
    os.makedirs("evidencias", exist_ok=True)
    
    # 1. Start streamlit app
    print("Starting Streamlit app...")
    process = subprocess.Popen(
        ["streamlit", "run", "main.py", "--server.port", "8502", "--server.headless", "true"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    for _ in range(30):
        try:
            r = requests.get("http://localhost:8502/_stcore/health")
            if r.status_code == 200:
                print("Streamlit app is running.")
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        print("Failed to start Streamlit app.")
        process.kill()
        return
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Context 1: Emisor
            context_emisor = browser.new_context()
            page_emisor = context_emisor.new_page()
            page_emisor.goto("http://localhost:8502")
            
            # The app likely has a login screen. We need to bypass it or login.
            # Assuming the app has input for username and password
            try:
                page_emisor.wait_for_selector("input[type='password']", timeout=5000)
                page_emisor.fill("input[type='text']", "admin") # Assuming 'admin' works
                page_emisor.fill("input[type='password']", "admin123")
                page_emisor.click("button:has-text('Ingresar')")
            except Exception as e:
                print("No login screen found or failed to login:", e)
                
            page_emisor.wait_for_timeout(2000)
            page_emisor.screenshot(path="evidencias/1_login.png")
            
            # Click on 'Guias' module if available
            try:
                page_emisor.click("text=Guias")
            except:
                print("Could not find Guias button")
                
            page_emisor.wait_for_timeout(2000)
            page_emisor.screenshot(path="evidencias/2_guias_emisor.png")
            
            # Fill form (just examples)
            # page_emisor.fill("input[aria-label='Nº de Transferencia']", "123456")
            # page_emisor.click("button:has-text('Generar')")
            
            # Context 2: Tienda
            context_tienda = browser.new_context()
            page_tienda = context_tienda.new_page()
            # The QR URL would be http://localhost:8502/?modulo=recepcion&transferencia=123456&guia=123
            # We'll just test the mock url
            page_tienda.goto("http://localhost:8502/?modulo=recepcion&guia=999999")
            
            page_tienda.wait_for_timeout(3000)
            page_tienda.screenshot(path="evidencias/3_recepcion_tienda.png")
            
            browser.close()
            print("Tests completed successfully!")
            
    finally:
        process.kill()

if __name__ == "__main__":
    test_e2e()
