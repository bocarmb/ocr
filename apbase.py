from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st
import os
import json
import io
import psycopg2
from psycopg2.extras import Json

# Chargez les variables d’environnement et configurez l’API-KEY google generativeai
load_dotenv()
genai.configure(api_key=os.getenv('API_KEY'))

# Connexion à la base de données PostgreSQL
#def connect_db():
   # return psycopg2.connect(
    #    dbname=os.getenv("DB_NAME"),
     #   user=os.getenv("DB_USER"),
     #   password=os.getenv("DB_PASSWORD"),
      #  host=os.getenv("DB_HOST"),
       # port=os.getenv("DB_PORT")
   # )
   
def connect_db():
    return psycopg2.connect(
        dbname=os.getenv("extraction_texte"),
        user=os.getenv("postgres"),
        password=os.getenv("bocar"),
        host=os.getenv("localhost"),
        port=os.getenv("5432")
    )
   # Connexion à PostgreSQL
#def connect_db():
    #return psycopg2.connect(
       # dbname="extraction_texte",
        #user="postgres",
        #="votre_mot_de_passe",
        #host="localhost",
        #port="5432"
    #)

def save_to_db(image_name, extracted_text):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO extracted_texts (image_name, extracted_text)
            VALUES (%s, %s)
        """, (image_name, Json(extracted_text)))
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Données enregistrées dans PostgreSQL.")
    except Exception as e:
        st.error(f"Erreur lors de l'insertion dans la base de données : {e}")
        



def load_image(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("Aucun fichier téléchargé")

# Définir la fonction de lecture d’images et conversion en PIL

def generate_text(image_data_list, input_prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")  # Remplacez par un modèle valide
    
    # Vérifier et convertir l'image en format compatible
    if isinstance(image_data_list, list) and len(image_data_list) > 0:
        image_dict = image_data_list[0]
        if isinstance(image_dict, dict) and 'data' in image_dict:
            image_bytes = image_dict['data']
            image = Image.open(io.BytesIO(image_bytes))  # Convertir en Image PIL
        else:
            raise ValueError("Format de données incorrect : clé 'data' manquante.")
    else:
        raise TypeError("Format incorrect : liste contenant un dictionnaire attendu.")
    
    # Générer une réponse avec le modèle
    response = model.generate_content([input_prompt, image])
    return response.text

# Définir la fonction d’enregistrement de sortie
def save_text_to_file(response, predefined_folder):
    if not os.path.exists(predefined_folder):
        os.makedirs(predefined_folder)
    file_path = os.path.join(predefined_folder, 'imageText.json')
    with open(file_path, 'w') as file:
        json.dump(response, file)

# Assurez-vous que les fonctions nécessaires sont définies ailleurs (comme load_image, generate_text, save_text_to_file)
def main():
    st.set_page_config(page_title="Image2Form")

    st.header("Transcrire l’image du formulaire rempli à la main en e-Form")
    uploaded_file = st.file_uploader("Choisir le fichier image pour détecter le texte", type=['jpeg', 'jpg', 'png'])
    
    image = None

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image téléchargée.", use_column_width=True)

    submit = st.button("Extraire le texte")

    input_prompt = """Lis le texte de l’image et affiche ce que tu vois
                      au format JSON selon les champs et les valeurs"""

    if submit and image:
        image_data = load_image(uploaded_file)
        response = generate_text(image_data, input_prompt)
        st.subheader("La réponse est")
        st.write(response)
        save_text_to_file(response, "./extractedText")
        save_to_db(uploaded_file.name, response)  # Enregistrer dans la base de données

if __name__ == "__main__":
    main()
