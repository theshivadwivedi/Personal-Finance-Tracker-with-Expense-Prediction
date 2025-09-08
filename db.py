import streamlit as st
from pymongo import MongoClient

MONGO_URI = st.secrets["MONGODB_URI"]
MONGO_DB = st.secrets["MONGODB_DB"]

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

users_col = db["users"]
expenses_col = db["expenses"]
