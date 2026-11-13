import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = "https://tdhvesgqjowgzkwcsofy.supabase.co/"
SUPABASE_KEY = "sb_publishable_ePVH6D7O0L88kY48WMHGjA_CN2SsnHZ"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

st.set_page_config(
    page_title="Control de Equipos | Mantenimiento",
    layout="wide"
)

st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
        }
        div.stButton > button {
            width: 100%;
            border-radius: 6px;
        }
    </style>
""", unsafe_allow_html=True)

st.sidebar.header("Panel de Búsqueda y Filtros")
st.sidebar.markdown("---")

equipos_res = supabase.table("equipos").select("*").execute()
equipos = equipos_res.data or []

if not equipos:
    st.warning("No hay equipos registrados en la tabla 'equipos'.")
    st.stop()

plantas_disponibles = ["Todas"] + sorted(list(set(str(eq.get('planta', 'Sin Planta')) for eq in equipos if eq.get('planta'))))
planta_seleccionada = st.sidebar.selectbox("Filtrar por Planta:", plantas_disponibles)

equipos_filtrados = equipos
if planta_seleccionada != "Todas":
    equipos_filtrados = [eq for eq in equipos_filtrados if str(eq.get('planta', 'Sin Planta')) == planta_seleccionada]

lineas_disponibles = ["Todas"] + sorted(list(set(str(eq.get('linea', 'Sin Línea')) for eq in equipos_filtrados if eq.get('linea'))))
linea_seleccionada = st.sidebar.selectbox("Filtrar por Línea:", lineas_disponibles)

if linea_seleccionada != "Todas":
    equipos_filtrados = [eq for eq in equipos_filtrados if str(eq.get('linea', 'Sin Línea')) == linea_seleccionada]

opciones_equipos = {}
for eq in equipos_filtrados:
    codigo = eq.get('Codigo de Activo', 'Sin Código')
    desc = eq.get('Equipo') or eq.get('descripcion_equipo') or ''
    label = f"{codigo} - {desc}" if desc else codigo
    opciones_equipos[label] = eq['id']

if not opciones_equipos:
    st.sidebar.warning("No hay equipos con los filtros seleccionados.")
    st.stop()

equipo_seleccionado_label = st.sidebar.selectbox("Seleccionar Equipo:", list(opciones_equipos.keys()))
id_equipo_actual = opciones_equipos[equipo_seleccionado_label]

equipo_info = next(eq for eq in equipos if eq['id'] == id_equipo_actual)
codigo_activo_actual = equipo_info.get('Codigo de Activo', 'N/A')

st.sidebar.markdown("---")
st.sidebar.info(f"Activo Seleccionado:\n`{codigo_activo_actual}`")

st.title(f"Gestión del Equipo: {codigo_activo_actual}")
st.markdown(f"**Ubicación / Planta:** {equipo_info.get('planta', 'N/A')} | **Línea:** {equipo_info.get('linea', 'N/A')}")

query_ref_asig = supabase.table("equipo_refacciones").select(
    "id, cantidad_requerida, refacciones(id, \"ITEM\", \"DESCRIPCION\", \"REFERENCIA\")"
).eq("registro_id", id_equipo_actual).execute()
ref_asignadas = query_ref_asig.data or []

historial_res = supabase.table("historial_equipos").select("*").eq("registro_id", id_equipo_actual).execute()
historial = historial_res.data or []

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric(label="Código de Activo", value=codigo_activo_actual)
col_m2.metric(label="Refacciones Vinculadas", value=len(ref_asignadas))
col_m3.metric(label="Eventos en Bitácora", value=len(historial))

st.markdown("")

tab1, tab2, tab3 = st.tabs([
    "Ficha, Planos y Refacciones", 
    "Asignar Refacción", 
    "Bitácora de Mantenimiento"
])

with tab1:
    col_f1, col_f2 = st.columns([1, 1])
    
    with col_f1:
        st.subheader("Archivos y Planos del Activo")
        
        archivo_actual = equipo_info.get('archivo_url')
        if archivo_actual:
            st.success("Este equipo cuenta con un archivo adjunto.")
            st.markdown(f"[Ver / Descargar Archivo Actual]({archivo_actual})")
            
            if any(archivo_actual.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                st.image(archivo_actual, caption="Foto / Plano del Activo", use_container_width=True)
        else:
            st.info("Este equipo no tiene planos o imágenes adjuntas.")
            
        with st.expander("Subir o actualizar plano / foto (Opcional)"):
            archivo_subido = st.file_uploader("Selecciona imagen o PDF", type=["png", "jpg", "jpeg", "pdf"])
            if st.button("Guardar Archivo en el Activo"):
                if archivo_subido is not None:
                    try:
                        file_path = f"{codigo_activo_actual}/{archivo_subido.name}"
                        
                        supabase.storage.from_("archivos_equipos").upload(
                            file_path, 
                            archivo_subido.getvalue(),
                            file_options={"upsert": "true"}
                        )
                        
                        public_url = supabase.storage.from_("archivos_equipos").get_public_url(file_path)
                        
                        supabase.table("equipos").update({"archivo_url": public_url}).eq("id", id_equipo_actual).execute()
                        
                        st.success("Archivo subido y asociado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al subir el archivo: {e}")
                else:
                    st.warning("Por favor selecciona un archivo primero.")

    with col_f2:
        st.subheader("Refacciones Asociadas al Equipo")
        if ref_asignadas:
            datos_tabla = []
            for item in ref_asignadas:
                ref_detalles = item.get("refacciones", {})
                if ref_detalles:
                    datos_tabla.append({
                        "ID Relación": item.get("id"),
                        "Ítem": ref_detalles.get("ITEM"),
                        "Descripción": ref_detalles.get("DESCRIPCION"),
                        "Referencia": ref_detalles.get("REFERENCIA"),
                        "Cantidad Req.": item.get("cantidad_requerida")
                    })
            if datos_tabla:
                st.dataframe(datos_tabla, use_container_width=True, hide_index=True)
                
                with st.expander("Desvincular refacción"):
                    opciones_desvincular = {f"Ítem {d['Ítem']} - {d['Descripción']}": d['ID Relación'] for d in datos_tabla}
                    id_relacion_a_borrar_label = st.selectbox("Selecciona:", list(opciones_desvincular.keys()))
                    id_relacion_a_borrar = opciones_desvincular[id_relacion_a_borrar_label]
                    
                    if st.button("Eliminar Asociación", type="secondary"):
                        try:
                            supabase.table("equipo_refacciones").delete().eq("id", id_relacion_a_borrar).execute()
                            st.success("Desvinculado con éxito.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.info("No hay refacciones asociadas.")

with tab2:
    st.subheader("Vincular Refacción del Catálogo Global")
    cat_ref_res = supabase.table("refacciones").select("id, \"ITEM\", \"DESCRIPCION\"").execute()
    catalogo = cat_ref_res.data
    
    if catalogo:
        with st.form("form_asignar_ref"):
            opciones_catalogo = {f"{r['ITEM']} - {r['DESCRIPCION']}": r['id'] for r in catalogo}
            ref_elegida_label = st.selectbox("Selecciona del catálogo global:", list(opciones_catalogo.keys()))
            id_ref_elegida = opciones_catalogo[ref_elegida_label]
            cantidad_req = st.number_input("Cantidad requerida:", min_value=1, value=1, step=1)
            
            if st.form_submit_button("Vincular Refacción al Equipo"):
                try:
                    supabase.table("equipo_refacciones").insert({
                        "registro_id": id_equipo_actual,
                        "refaccion_id": id_ref_elegida,
                        "cantidad_requerida": cantidad_req
                    }).execute()
                    st.success("Refacción asignada con éxito.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al asignar: {e}")
    else:
        st.warning("El catálogo global de refacciones está vacío.")

with tab3:
    col_h1, col_h2 = st.columns([2, 1])
    
    with col_h1:
        st.subheader("Historial de Eventos")
        historial_ordenado = sorted(historial, key=lambda x: x.get('created_at', ''), reverse=True)
        
        if historial_ordenado:
            for evento in historial_ordenado:
                with st.container(border=True):
                    tipo = evento.get('tipo_evento', 'General')
                    st.markdown(f"**Tipo:** `{tipo}`  |  *{evento.get('created_at', '')[:19]}*")
                    st.markdown(f"{evento.get('descripcion', '')}")
                    if evento.get('tecnico'):
                        st.caption(f"Registrado por: {evento.get('tecnico')}")
        else:
            st.info("No hay eventos registrados en la bitácora de este equipo.")
            
    with col_h2:
        st.subheader("Registrar Evento")
        with st.form("form_bitacora"):
            tipo_evento = st.selectbox("Tipo de Evento", [
                "Mantenimiento Preventivo", 
                "Mantenimiento Correctivo", 
                "Falla Reportada", 
                "Cambio de Componente", 
                "Inspección"
            ])
            descripcion_evento = st.text_area("Detalle de lo realizado / Suceso")
            nombre_tecnico = st.text_input("Técnico Responsable")
            
            if st.form_submit_button("Guardar en la Bitácora"):
                if descripcion_evento.strip():
                    try:
                        supabase.table("historial_equipos").insert({
                            "registro_id": id_equipo_actual,
                            "tipo_evento": tipo_evento,
                            "descripcion": descripcion_evento,
                            "tecnico": nombre_tecnico
                        }).execute()
                        st.success("Guardado en la bitácora.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("La descripción no puede estar vacía.")