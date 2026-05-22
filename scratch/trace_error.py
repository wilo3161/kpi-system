import sys
import os
import traceback

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock Streamlit elements before importing anything
import streamlit as st

class MockSecrets(dict):
    def __getattr__(self, name): return self.get(name, None)
    def __getitem__(self, name): return self.get(name, None)
st.secrets = MockSecrets()

class MockSessionState(dict):
    def __getattr__(self, name): return self.get(name, None)
    def __setattr__(self, name, val): self[name] = val
st.session_state = MockSessionState()
st.session_state['role'] = 'Administrador'
st.session_state['username'] = 'admin'

from modules.main_page import show_main_page

try:
    print("Executing show_main_page()...")
    show_main_page()
    print("Execution completed successfully without errors!")
except Exception as e:
    print("Caught Exception:")
    traceback.print_exc()
