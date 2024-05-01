import streamlit as st
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(initial_sidebar_state="collapsed")
no_sidebar_style = """
    <style>
        div[data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(no_sidebar_style, unsafe_allow_html=True)


st.header("Welcome back...! ")
st.subheader("HR Insight Bot: Your Virtual HR Assistant 🤝")


username = st.text_input("Username")
password = st.text_input("Password",type='password')

if st.button("Login"):
    if username == "employee" and password == "employee":
        st.success("login successfull")
        switch_page('Employee Interface')
    else:
        st.error("Login Failed - Please check the Username and Password")

st.warning("Contact IT Desk on 2222 or itsupportdesk@abc.com | Click www.abc.com to see the FAQ")