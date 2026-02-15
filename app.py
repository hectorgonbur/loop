import streamlit as st
import datetime
import io
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, LargeBinary, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# ----------------------------
# Configuración de la base de datos
# ----------------------------
engine = create_engine('sqlite:///archihub.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# ----------------------------
# Modelos SQLAlchemy
# ----------------------------
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer)           # año de cursada (1-6)
    current_catedra = Column(String) # cátedra actual de arquitectura

class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer)           # año al que pertenece la materia (1-6)

class Catedra(Base):
    __tablename__ = 'catedras'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'))

class TP(Base):
    __tablename__ = 'tps'
    id = Column(Integer, primary_key=True)
    name = Column(String)            # ej. "TP1", "TP2", ...
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    order = Column(Integer)          # para mantener orden

class UserTP(Base):
    __tablename__ = 'user_tps'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    tp_id = Column(Integer, ForeignKey('tps.id'))
    state = Column(String)            # "Pendiente", "Entregado", "Aprobado"

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    image = Column(LargeBinary)       # imagen en bytes
    caption = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Like(Base):
    __tablename__ = 'likes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    post_id = Column(Integer, ForeignKey('posts.id'))

class Resource(Base):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    title = Column(String)
    description = Column(Text)

class Rating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    catedra_id = Column(Integer, ForeignKey('catedras.id'))
    rating = Column(Integer)          # 1 a 5
    comment = Column(Text)

# ----------------------------
# Crear tablas y datos iniciales
# ----------------------------
def init_db():
    Base.metadata.create_all(engine)
    session = Session()

    # Cargar materias de ejemplo (solo 1er año)
    if session.query(Subject).count() == 0:
        materias_primer_anio = [
            "Taller de Arquitectura I",
            "Matemática I",
            "Física I",
            "Historia I",
            "Gráfica I"
        ]
        for nombre in materias_primer_anio:
            subject = Subject(name=nombre, year=1)
            session.add(subject)
        session.commit()

        # Agregar TPs a cada materia (3 por materia)
        subjects = session.query(Subject).all()
        for subj in subjects:
            for i in range(1, 4):
                tp = TP(name=f"TP{i}", subject_id=subj.id, order=i)
                session.add(tp)
        session.commit()

        # Agregar cátedras para Taller de Arquitectura I
        taller = session.query(Subject).filter_by(name="Taller de Arquitectura I").first()
        if taller:
            for nombre_catedra in ["Szelagowski", "Bares", "Gandolfi"]:
                catedra = Catedra(name=nombre_catedra, subject_id=taller.id)
                session.add(catedra)
        session.commit()

        # Agregar algún recurso de ejemplo
        for subj in subjects:
            recurso = Resource(subject_id=subj.id, title=f"Apunte de {subj.name}", description="Descripción breve del apunte.")
            session.add(recurso)
        session.commit()

        # Crear un usuario de prueba
        if session.query(User).count() == 0:
            user = User(name="Estudiante Ejemplo", year=1, current_catedra="Szelagowski")
            session.add(user)
            session.commit()

            # Asignar algunos estados de TP para el usuario de prueba
            tps = session.query(TP).all()
            for tp in tps[:3]:  # algunos aprobados, otros pendientes
                user_tp = UserTP(user_id=user.id, tp_id=tp.id, state="Aprobado")
                session.add(user_tp)
            for tp in tps[3:6]:
                user_tp = UserTP(user_id=user.id, tp_id=tp.id, state="Pendiente")
                session.add(user_tp)
            session.commit()

    session.close()

# ----------------------------
# Funciones de ayuda
# ----------------------------
def get_user_name(user_id):
    session = Session()
    user = session.query(User).get(user_id)
    session.close()
    return user.name if user else ""

def get_subjects_by_year(year):
    session = Session()
    subjects = session.query(Subject).filter_by(year=year).all()
    session.close()
    return subjects

def get_tps_for_subject(subject_id):
    session = Session()
    tps = session.query(TP).filter_by(subject_id=subject_id).order_by(TP.order).all()
    session.close()
    return tps

def get_user_tp_state(user_id, tp_id):
    session = Session()
    user_tp = session.query(UserTP).filter_by(user_id=user_id, tp_id=tp_id).first()
    state = user_tp.state if user_tp else "Pendiente"
    session.close()
    return state

def update_user_tp_state(user_id, tp_id, new_state):
    session = Session()
    user_tp = session.query(UserTP).filter_by(user_id=user_id, tp_id=tp_id).first()
    if user_tp:
        user_tp.state = new_state
    else:
        user_tp = UserTP(user_id=user_id, tp_id=tp_id, state=new_state)
        session.add(user_tp)
    session.commit()
    session.close()

def get_progress_for_subject(user_id, subject_id):
    tps = get_tps_for_subject(subject_id)
    if not tps:
        return 0.0
    approved = 0
    for tp in tps:
        if get_user_tp_state(user_id, tp.id) == "Aprobado":
            approved += 1
    return approved / len(tps)

# ----------------------------
# Página de login / registro
# ----------------------------
def login_page():
    st.title("LOOP")
    st.markdown("Bienvenido a la plataforma de organización y comunidad para estudiantes.")

    with st.form("login_form"):
        name = st.text_input("Nombre")
        year = st.selectbox("Año de cursada", [1,2,3,4,5,6])
        catedra = st.text_input("Cátedra actual de Arquitectura (ej. Szelagowski)")
        submitted = st.form_submit_button("Ingresar")

    if submitted and name:
        session = Session()
        user = session.query(User).filter_by(name=name).first()
        if not user:
            user = User(name=name, year=year, current_catedra=catedra)
            session.add(user)
            session.commit()
        st.session_state.user_id = user.id
        session.close()
        st.rerun()
    elif submitted:
        st.error("Por favor ingresa tu nombre.")

# ----------------------------
# Dashboard académico (Mi Cursada)
# ----------------------------
def dashboard_page():
    st.header("Mi Cursada")
    user_id = st.session_state.user_id

    # Pestañas por año
    años = list(range(1,7))
    tabs = st.tabs([f"Año {a}" for a in años])

    for i, año in enumerate(años):
        with tabs[i]:
            subjects = get_subjects_by_year(año)
            if not subjects:
                st.info("No hay materias cargadas para este año.")
            for subj in subjects:
                with st.expander(f"**{subj.name}**"):
                    tps = get_tps_for_subject(subj.id)
                    if not tps:
                        st.write("No hay TPs definidos.")
                    else:
                        # Formulario para actualizar estados
                        with st.form(key=f"form_{subj.id}"):
                            states = {}
                            for tp in tps:
                                current_state = get_user_tp_state(user_id, tp.id)
                                new_state = st.selectbox(
                                    f"{tp.name}",
                                    ["Pendiente", "Entregado", "Aprobado"],
                                    index=["Pendiente", "Entregado", "Aprobado"].index(current_state),
                                    key=f"tp_{subj.id}_{tp.id}"
                                )
                                states[tp.id] = new_state

                            if st.form_submit_button("Guardar progreso"):
                                for tp_id, new_state in states.items():
                                    update_user_tp_state(user_id, tp_id, new_state)
                                st.success("Progreso guardado!")
                                st.rerun()

                        # Barra de progreso
                        progress = get_progress_for_subject(user_id, subj.id)
                        st.progress(progress, text=f"Progreso: {int(progress*100)}% completado")

# ----------------------------
# Feed social (estilo Instagram)
# ----------------------------
def social_feed_page():
    st.header("Feed Social")
    user_id = st.session_state.user_id

    # Formulario para nuevo post
    with st.expander("Subir nueva imagen"):
        with st.form("new_post_form"):
            uploaded_file = st.file_uploader("Elige una imagen", type=["jpg", "jpeg", "png"])
            subject_id = st.selectbox(
                "Materia relacionada",
                options=[(s.id, s.name) for s in Session().query(Subject).all()],
                format_func=lambda x: x[1]
            )
            caption = st.text_area("Descripción")
            submitted = st.form_submit_button("Publicar")

            if submitted and uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                session = Session()
                new_post = Post(
                    user_id=user_id,
                    subject_id=subject_id[0],
                    image=bytes_data,
                    caption=caption
                )
                session.add(new_post)
                session.commit()
                session.close()
                st.success("Post publicado!")
                st.rerun()

    # Mostrar posts en orden cronológico inverso
    session = Session()
    posts = session.query(Post).order_by(Post.created_at.desc()).all()
    for post in posts:
        col1, col2 = st.columns([1, 3])
        with col1:
            if post.image:
                st.image(post.image, use_container_width=True)
            else:
                st.write("Sin imagen")
        with col2:
            autor = session.query(User).get(post.user_id).name
            materia = session.query(Subject).get(post.subject_id).name
            st.markdown(f"**{autor}** · *{materia}*")
            st.caption(post.caption)
            likes = session.query(Like).filter_by(post_id=post.id).count()
            liked = session.query(Like).filter_by(post_id=post.id, user_id=user_id).first() is not None

            col_like, col_count = st.columns([1, 5])
            with col_like:
                if st.button("❤️" if liked else "🤍", key=f"like_{post.id}"):
                    if liked:
                        # Quitar like
                        session.query(Like).filter_by(post_id=post.id, user_id=user_id).delete()
                    else:
                        new_like = Like(post_id=post.id, user_id=user_id)
                        session.add(new_like)
                    session.commit()
                    st.rerun()
            with col_count:
                st.write(f"{likes} likes")
        st.divider()
    session.close()

# ----------------------------
# Perfil con portfolio
# ----------------------------
def profile_page():
    st.header("Mi Perfil")
    user_id = st.session_state.user_id
    session = Session()
    user = session.query(User).get(user_id)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(user.name)
        st.write(f"Año de cursada: {user.year}")
        st.write(f"Cátedra: {user.current_catedra}")
    with col2:
        # Promedio académico (simulado)
        st.metric("Promedio Académico", "7.5")

    # Grid de posts del usuario (portfolio)
    st.subheader("Mis Publicaciones")
    user_posts = session.query(Post).filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    if user_posts:
        cols = st.columns(3)
        for i, post in enumerate(user_posts):
            # Cambia esto en tu función profile_page:
            with cols[i % 3]:
                if post.image:
                    # Usa un borde y ajusta el tamaño para que parezca una grilla de Instagram
                    st.image(post.image, use_container_width=True, caption=f"Materia: {materia}")
                else:
                    st.write("Imagen no disponible")
    else:
        st.info("Aún no has publicado nada.")

    session.close()

# ----------------------------
# Repositorio de apuntes
# ----------------------------
def resources_page():
    st.header("Repositorio de Apuntes")

    session = Session()
    subjects = session.query(Subject).all()
    subject_dict = {s.id: s.name for s in subjects}

    # Selector de materia
    selected_subject_id = st.selectbox(
        "Filtrar por materia",
        options=list(subject_dict.keys()),
        format_func=lambda x: subject_dict[x]
    )

    # Mostrar recursos de esa materia
    resources = session.query(Resource).filter_by(subject_id=selected_subject_id).all()
    for res in resources:
        with st.container(border=True):
            st.markdown(f"**{res.title}**")
            st.write(res.description)
            st.button("Ver/Descargar", key=f"res_{res.id}")

    # Formulario para agregar recurso (simulado)
    with st.expander("Agregar nuevo apunte"):
        with st.form("new_resource"):
            title = st.text_input("Título")
            desc = st.text_area("Descripción")
            if st.form_submit_button("Subir"):
                new_res = Resource(subject_id=selected_subject_id, title=title, description=desc)
                session.add(new_res)
                session.commit()
                st.success("Apunte agregado!")
                st.rerun()

    session.close()

# ----------------------------
# Ranking de cátedras
# ----------------------------
def ranking_page():
    st.header("Ranking de Cátedras")
    user_id = st.session_state.user_id
    session = Session()

    # Mostrar todas las cátedras con promedio
    catedras = session.query(Catedra).all()
    for cat in catedras:
        materia = session.query(Subject).get(cat.subject_id).name
        avg_rating = session.query(func.avg(Rating.rating)).filter_by(catedra_id=cat.id).scalar()
        avg_rating = round(avg_rating, 1) if avg_rating else "Sin reseñas"

        with st.container(border=True):
            st.markdown(f"**{cat.name}** - {materia}")
            st.write(f"Valoración promedio: {avg_rating} ⭐")

            # Ver si el usuario ya calificó
            user_rating = session.query(Rating).filter_by(user_id=user_id, catedra_id=cat.id).first()
            if user_rating:
                st.write(f"Tu calificación: {user_rating.rating} estrellas")
                if st.button("Editar", key=f"edit_{cat.id}"):
                    # Simplemente borramos para que pueda volver a calificar
                    session.delete(user_rating)
                    session.commit()
                    st.rerun()
            else:
                with st.form(key=f"rate_{cat.id}"):
                    rating = st.select_slider("Puntuación", options=[1,2,3,4,5], value=3, key=f"slider_{cat.id}")
                    comment = st.text_area("Comentario (opcional)", key=f"comm_{cat.id}")
                    if st.form_submit_button("Calificar"):
                        new_rating = Rating(user_id=user_id, catedra_id=cat.id, rating=rating, comment=comment)
                        session.add(new_rating)
                        session.commit()
                        st.success("¡Gracias por tu reseña!")
                        st.rerun()
    session.close()

# ----------------------------
# Navegación principal
# ----------------------------
def main():
    init_db()

    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    if st.session_state.user_id is None:
        login_page()
    else:
        st.sidebar.title("ARCHI-HUB")
        menu = st.sidebar.radio(
            "Navegación",
            ["Mi Cursada", "Feed Social", "Perfil", "Recursos", "Ranking"]
        )

        if menu == "Mi Cursada":
            dashboard_page()
        elif menu == "Feed Social":
            social_feed_page()
        elif menu == "Perfil":
            profile_page()
        elif menu == "Recursos":
            resources_page()
        elif menu == "Ranking":
            ranking_page()

if __name__ == "__main__":
    st.set_page_config(page_title="LOOP", layout="wide")
    # Modo oscuro por defecto (Streamlit ya lo respeta según configuración del sistema)
    # Forzamos tema oscuro con CSS personalizado (opcional)
    st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    </style>
    """, unsafe_allow_html=True)
    main()
