import hashlib
import os
import random
import sqlite3
import streamlit as st

st.set_page_config(
    page_title="Catalog Școlar Inteligent",
    page_icon="🎓",
    layout="centered",
)

if not os.path.exists("uploads"):
  os.makedirs("uploads")

PAROLA_HASH_SECRET = (
    "acec72785caa9d12059f773773294e3bdd8259c511cb1a1dee91900366f0bbca"
)


def cripteaza(text):
  return hashlib.sha256(text.encode()).hexdigest()


if "authenticated" not in st.session_state:
  st.session_state.authenticated = False

if not st.session_state.authenticated:
  st.title("🔒 Acces Restricționat - Catalog Școlar")
  st.write("Te rog să introduci parola pentru a debloca aplicația.")

  parola_introdusa = st.text_input("Parolă:", type="password")
  if st.button("Autentificare"):
    if cripteaza(parola_introdusa) == PAROLA_HASH_SECRET:
      st.session_state.authenticated = True
      st.rerun()
    else:
      st.error("❌ Parolă incorectă! Încearcă din nou.")

  st.stop()


def init_db():
  conn = sqlite3.connect("catalog_web.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS elevi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nume TEXT NOT NULL,
            prezenta TEXT DEFAULT 'Absent',
            tema INTEGER DEFAULT 0,
            tema_suplimentara INTEGER DEFAULT 0,
            poza TEXT
        )
    """)
  try:
    cursor.execute("ALTER TABLE elevi ADD COLUMN poza TEXT")
  except:
    pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS note (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            elev_id INTEGER,
            nota REAL,
            FOREIGN KEY (elev_id) REFERENCES elevi (id) ON DELETE CASCADE
        )
    """)
  conn.commit()
  conn.close()


init_db()


def verifica_easter_egg():
  contador_file = "launch_count.txt"
  count = 1
  if os.path.exists(contador_file):
    try:
      with open(contador_file, "r") as f:
        count = int(f.read().strip()) + 1
    except:
      count = 1

  with open(contador_file, "w") as f:
    f.write(str(count))

  return count >= 100


if "secret_active" not in st.session_state:
  st.session_state.secret_active = verifica_easter_egg()

if st.session_state.secret_active:
  bg_main = "rgb(254, 240, 138)"
  text_color = "rgb(30, 41, 59)"
  title_text = "🦄 Catalog Școlar - PETRECERE 100! 🎊"
elif "dark_mode" in st.session_state and st.session_state.dark_mode:
  bg_main = "rgb(15, 23, 42)"
  text_color = "rgb(248, 250, 252)"
  title_text = "🎓 Catalog Școlar Inteligent (Dark)"
else:
  bg_main = "rgb(248, 250, 252)"
  text_color = "rgb(30, 41, 59)"
  title_text = "🎓 Catalog Școlar Inteligent"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_main};
    }}
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] {{
        color: {text_color} !important;
    }}
    .streamlit-expanderHeader {{
        color: {text_color} !important;
    }}
    </style>
""",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([3, 1])

with col1:
  if st.button(title_text, key="titlu_btn"):
    if "click_count" not in st.session_state:
      st.session_state.click_count = 0
    st.session_state.click_count += 1
    if st.session_state.click_count >= 5:
      st.session_state.secret_active = True
      st.rerun()

with col2:
  if st.session_state.secret_active:
    if st.button("❌ Dezactivează Secret"):
      st.session_state.secret_active = False
      if os.path.exists("launch_count.txt"):
        os.remove("launch_count.txt")
      st.rerun()
  else:
    current_dark = st.session_state.get("dark_mode", False)
    btn_label = "☀️ Light" if current_dark else "🌙 Dark"
    if st.button(btn_label):
      st.session_state.dark_mode = not current_dark
      st.rerun()

if st.session_state.secret_active:
  st.balloons()

st.markdown("---")

st.subheader("➕ Adaugă Elev Nou")
with st.form("form_elev", clear_on_submit=True):
  nume_nou = st.text_input("Nume și Prenume Elev:")
  foto_incarcata = st.file_uploader(
      "Încarcă poză elev (opțional):", type=["png", "jpg", "jpeg"]
  )
  submit_elev = st.form_submit_button("Adaugă în Catalog")

  if submit_elev:
    if nume_nou.strip():
      foto_path = None
      if foto_incarcata is not None:
        foto_path = os.path.join("uploads", foto_incarcata.name)
        with open(foto_path, "wb") as f:
          f.write(foto_incarcata.getbuffer())

      conn = sqlite3.connect("catalog_web.db", check_same_thread=False)
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO elevi (nume, poza) VALUES (?, ?)",
          (nume_nou.strip(), foto_path),
      )
      conn.commit()
      conn.close()
      st.success(f"Elevul {nume_nou} a fost adăugat cu succes!")
      st.rerun()
    else:
      st.warning("Te rog introdu un nume valid.")

st.markdown("---")

st.subheader("📋 Lista Elevi și Situația Școlară")

conn = sqlite3.connect("catalog_web.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    "SELECT id, nume, prezenta, tema, tema_suplimentara, poza FROM elevi"
)
elevi = cursor.fetchall()
conn.close()

if not elevi:
  st.info("Nu există elevi adăugați momentan în catalog.")
else:
  for elev_id, nume, prezenta, tema, tema_supl, poza in elevi:
    with st.expander(f"👤 {nume}  |  Prezență: {prezenta}"):

      if poza and os.path.exists(poza):
        st.image(poza, width=120)

      conn = sqlite3.connect("catalog_web.db", check_same_thread=False)
      cursor = conn.cursor()
      cursor.execute("SELECT id, nota FROM note WHERE elev_id = ?", (elev_id,))
      note_db = cursor.fetchall()
      conn.close()

      note_valori = [n[1] for n in note_db]
      medie = (
          round(sum(note_valori) / len(note_valori), 2)
          if note_valori
          else "Fără note"
      )

      col_info1, col_info2 = st.columns(2)
      with col_info1:
        st.write(f"**Media generală:** {medie}")
        st.write(f"**Temă normală:** {'✅ Da' if tema == 1 else '❌ Nu'}")
        st.write(
            f"**Temă suplimentară:** {'✅ Da' if tema_supl == 1 else '❌ Nu'}"
        )

      with col_info2:
        noua_prezenta = st.radio(
            "Prezență:",
            ["Prezent", "Absent"],
            index=0 if prezenta == "Prezent" else 1,
            key=f"p_{elev_id}",
        )
        if noua_prezenta != prezenta:
          conn = sqlite3.connect("catalog_web.db", check_same_thread=False)
          cursor = conn.cursor()
          cursor.execute(
              "UPDATE elevi SET prezenta = ? WHERE id = ?",
              (noua_prezenta, elev_id),
          )
          conn.commit()
          conn.close()
          st.rerun()

      st.markdown("##### 📝 Adaugă o notă nouă")
      c_nota, c_btn = st.columns([2, 1])
      with c_nota:
        nota_noua = st.number_input(
            "Notă (1-10):",
            min_value=1.0,
            max_value=10.0,
            step=0.5,
            value=10.0,
            key=f"nota_input_{elev_id}",
        )
      with c_btn:
        st.write("")
        st.write("")
        if st.button("Salvează Notă", key=f"btn_nota_{elev_id}"):
          conn = sqlite3.connect("catalog_web.db", check_same_thread=False)
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO note (elev_id, nota) VALUES (?, ?)",
              (elev_id, nota_noua),
          )
          conn.commit()
          conn.close()
          st.success("Notă adăugată!")
          st.rerun()

      st.markdown("##### 📚 Verificare Teme")
      col_t1, col_t2 = st.columns(2)
      with col_t1:
        t_norm = st.checkbox(
            "Temă normală făcută", value=bool(tema), key=f"chk_t_{elev_id}"
        )
      with col_t2:
        t_supl = st.checkbox(
            "Temă suplimentară făcută",
            value=bool(tema_supl),
            key=f"chk_s_{elev_id}",
        )

      if st.button("Salvează Teme", key=f"btn_salv_t_{elev_id}"):
        conn = sqlite3.connect("catalog_web.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE elevi SET tema = ?, tema_suplimentara = ? WHERE id = ?",
            (int(t_norm), int(t_supl), elev_id),
        )
        conn.commit()
        conn.close()
        st.success("Teme actualizate!")
        st.rerun()

      if st.button(f"🗑️ Șterge elevul {nume}", key=f"del_{elev_id}"):
        conn = sqlite3.connect("catalog_web.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM elevi WHERE id = ?", (elev_id,))
        cursor.execute("DELETE FROM note WHERE elev_id = ?", (elev_id,))
        conn.commit()
        conn.close()
        st.warning("Elevul a fost șters.")
        st.rerun()
