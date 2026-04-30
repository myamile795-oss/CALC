import streamlit as st

# Título
st.title("Mi primera app con Streamlit 🚀")

# Texto
st.write("Escribe tu nombre:")

# Input del usuario
nombre = st.text_input("Nombre")

# Botón
if st.button("Saludar"):
    if nombre:
        st.success(f"Hola, {nombre}! 👋")
    else:
        st.warning("Escribe tu nombre primero 😅")

# Slider
edad = st.slider("Selecciona tu edad", 0, 100, 18)
st.write(f"Tienes {edad} años")