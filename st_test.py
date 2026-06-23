import streamlit as st
from database.manager import local_db
import json

with open("mongo_status.txt", "w") as f:
    f.write(str(getattr(local_db, 'connected', False)))
    
st.write("Mongo Connected:", getattr(local_db, 'connected', False))
