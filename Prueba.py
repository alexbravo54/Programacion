import streamlit as st
import pandas as pd
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

# ---------------------------------------------------------------------------
# Estilo corporativo y optimización visual
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    :root {
        --navy: #14213D;
        --navy-2: #1D2D50;
        --navy-line: #34456B;
        --bg: #F4F6F9;
        --panel-head: #EEF1F5;
        --line: #D5DBE4;
        --txt: #1B2433;
        --txt-2: #5B6678;
        --side-txt: #9AA7BD;
    }

    /* Base */
    .stApp { background: var(--bg); }
    .block-container { padding-top: 2rem; max-width: 1450px; }
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDeployButton"] { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    /* Barra lateral */
    [data-testid="stSidebar"] { background: var(--navy); border-right: 1px solid var(--navy); }
    [data-testid="stSidebar"] label p {
        color: var(--side-txt) !important;
        font-size: 12px !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: var(--navy-2);
        border: 1px solid var(--navy-line);
        border-radius: 2px;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] div[data-baseweb="select"] svg { fill: #FFFFFF; }
    .sb-title {
        color: #FFFFFF; font-size: 13px; font-weight: 500;
        letter-spacing: .06em; margin: 0 0 4px 0;
    }
    .sb-sub {
        color: var(--side-txt); font-size: 11px; margin: 0 0 8px 0;
        padding-bottom: 14px; border-bottom: 1px solid #2C3B5E;
    }
    .sb-activo {
        margin-top: 24px; padding: 10px 12px;
        border: 1px solid var(--navy-line); border-left: 3px solid #FFFFFF;
    }
    .sb-activo small { display: block; color: var(--side-txt); font-size: 11px; }
    .sb-activo b { color: #FFFFFF; font-size: 15px; font-weight: 500; }

    /* Encabezado de la página */
    .crumb { font-size: 12px; color: var(--txt-2); margin-bottom: 6px; }
    .titulo { font-size: 26px; font-weight: 500; color: var(--navy); margin: 0 0 4px 0; }
    .subtitulo { font-size: 13px; color: #3B465A; margin-bottom: 22px; }

    /* Indicadores */
    [data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid var(--line);
        border-top: 3px solid var(--navy); padding: 12px 14px;
    }
    [data-testid="stMetricLabel"] p { font-size: 12px; color: var(--txt-2); }
    [data-testid="stMetricValue"] { font-size: 22px; font-weight: 500; color: var(--navy); }

    /* Pestañas */
    div[data-baseweb="tab-list"] { gap: 28px; margin-bottom: 10px; }
    button[data-baseweb="tab"] p { font-size: 13px; color: var(--txt-2); }
    button[data-baseweb="tab"][aria-selected="true"] p { color: var(--navy); font-weight: 500; }
    div[data-baseweb="tab-highlight"] { background-color: var(--navy); height: 3px; }
    div[data-baseweb="tab-border"] { background-color: #CBD2DC; }

    /* Paneles y avisos */
    .ph {
        padding: 10px 14px; font-size: 13px; font-weight: 500; color: var(--navy);
        background: var(--panel-head); border: 1px solid var(--line);
        margin: 0 0 0 0;
    }
    .aviso {
        padding: 14px; font-size: 13px; color: var(--txt-2);
        background: #FFFFFF; border: 1px solid var(--line);
        border-top: none; margin-bottom: 12px;
    }
    .aviso.ok    { border-left: 3px solid #2F6B4F; color: var(--txt); }
    .aviso.warn  { border-left: 3px solid #8A5A00; color: var(--txt); }
    .aviso.error { border-left: 3px solid #9B1C1C; color: var(--txt); }
    .aviso.suelto { border-top: 1px solid var(--line); }

    /* Controles */
    div.stButton > button,
    [data-testid="stFormSubmitButton"] > button {
        width: 100%; border-radius: 2px;
        background: var(--navy); color: #FFFFFF; border: 1px solid var(--navy);
        font-size: 13px;
    }
    div.stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: var(--navy-2); border-color: var(--navy-2); color: #FFFFFF;
    }
    div[data-baseweb="input"], div[data-baseweb="textarea"] { border-radius: 2px; }
    div[data-baseweb="select"] > div { border-radius: 2px; }
    [data-testid="stExpander"], [data-testid="stForm"] {
        background: #FFFFFF; border: 1px solid var(--line); border-radius: 0;
    }
    [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 0; }
    h3 { font-size: 15px !important; font-weight: 500 !important; color: var(--navy); margin-top: 0px !important; }
</style>
""", unsafe_allow_html=True)


def aviso(texto, tipo="info", suelto=False):
    clases = f"aviso {tipo}" + (" suelto" if suelto else "")
    st.markdown(f'<div class="{clases}">{texto}</div>', unsafe_allow_html=True)


def encabezado_panel(texto):
    st.markdown(f'<div class="ph">{texto}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Carga de datos y lectura de parámetros URL (QR)
# ---------------------------------------------------------------------------
equipos_res = supabase.table("equipos").select("*").execute()
equipos = equipos_res.data or []

if not equipos:
    aviso("No hay equipos registrados en la tabla 'equipos'.", "warn", suelto=True)
    st.stop()

query_params = st.query_params
id_equipo_en_url = query_params.get("equipo", None)

equipo_encontrado_por_qr = None
if id_equipo_en_url is not None:
    try:
        id_url_int = int(id_equipo_en_url)
        equipo_encontrado_por_qr = next((eq for eq in equipos if eq.get('id') == id_url_int), None)
    except ValueError:
        pass

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    '<p class="sb-title">GESTIÓN DE ACTIVOS</p>'
    '<p class="sb-sub">Búsqueda y filtros</p>',
    unsafe_allow_html=True
)

plantas_disponibles = ["Todas"] + sorted(list(set(str(eq.get('planta', 'Sin Planta')) for eq in equipos if eq.get('planta'))))

planta_por_defecto = 0
if equipo_encontrado_por_qr and equipo_encontrado_por_qr.get('planta') in plantas_disponibles:
    planta_por_defecto = plantas_disponibles.index(equipo_encontrado_por_qr.get('planta'))

planta_seleccionada = st.sidebar.selectbox("Planta", plantas_disponibles, index=planta_por_defecto)

equipos_filtrados = equipos
if planta_seleccionada != "Todas":
    equipos_filtrados = [eq for eq in equipos_filtrados if str(eq.get('planta', 'Sin Planta')) == planta_seleccionada]

lineas_disponibles = ["Todas"] + sorted(list(set(str(eq.get('linea', 'Sin Línea')) for eq in equipos_filtrados if eq.get('linea'))))

linea_por_defecto = 0
if equipo_encontrado_por_qr and equipo_encontrado_por_qr.get('linea') in lineas_disponibles:
    linea_por_defecto = lineas_disponibles.index(equipo_encontrado_por_qr.get('linea'))

linea_seleccionada = st.sidebar.selectbox("Línea", lineas_disponibles, index=linea_por_defecto)

if linea_seleccionada != "Todas":
    equipos_filtrados = [eq for eq in equipos_filtrados if str(eq.get('linea', 'Sin Línea')) == linea_seleccionada]

opciones_equipos = {}
indice_equipo_select = 0

for idx, eq in enumerate(equipos_filtrados):
    codigo = eq.get('Codigo de Activo', 'Sin Código')
    desc = eq.get('Equipo') or eq.get('descripcion_equipo') or ''
    label = f"{codigo} - {desc}" if desc else codigo
    opciones_equipos[label] = eq['id']
    
    if equipo_encontrado_por_qr and eq['id'] == equipo_encontrado_por_qr['id']:
        indice_equipo_select = idx

if not opciones_equipos:
    with st.sidebar:
        aviso("No hay equipos con los filtros seleccionados.", "warn", suelto=True)
    st.stop()

equipo_seleccionado_label = st.sidebar.selectbox("Equipo", list(opciones_equipos.keys()), index=indice_equipo_select)
id_equipo_actual = opciones_equipos[equipo_seleccionado_label]

equipo_info = next(eq for eq in equipos if eq['id'] == id_equipo_actual)
codigo_activo_actual = equipo_info.get('Codigo de Activo', 'N/A')
descripcion_actual = equipo_info.get('Equipo') or equipo_info.get('descripcion_equipo') or ''

st.sidebar.markdown(
    f'<div class="sb-activo"><small>Activo seleccionado</small><b>{codigo_activo_actual}</b></div>',
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------------
# Encabezado principal limpio
# ---------------------------------------------------------------------------
st.markdown(
    f'<div class="crumb">Activos / Equipos / {codigo_activo_actual}</div>'
    f'<div class="titulo">Equipo {codigo_activo_actual}</div>',
    unsafe_allow_html=True
)
partes_sub = []
if descripcion_actual:
    partes_sub.append(str(descripcion_actual))
partes_sub.append(f"Planta: {equipo_info.get('planta', 'N/A')}")
partes_sub.append(f"Línea: {equipo_info.get('linea', 'N/A')}")
st.markdown(f'<div class="subtitulo">{"  |  ".join(partes_sub)}</div>', unsafe_allow_html=True)

query_ref_asig = supabase.table("equipo_refacciones").select(
    "id, cantidad_requerida, created_at, refacciones(id, \"ITEM\", \"DESCRIPCION\", \"REFERENCIA\")"
).eq("registro_id", id_equipo_actual).execute()
ref_asignadas = query_ref_asig.data or []

historial_res = supabase.table("historial_equipos").select("*").eq("registro_id", id_equipo_actual).execute()
historial = historial_res.data or []

archivos_res = supabase.table("archivos_equipos").select("*").eq("registro_id", id_equipo_actual).execute()
lista_archivos = archivos_res.data or []

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric(label="Código de activo", value=codigo_activo_actual)
col_m2.metric(label="Refacciones vinculadas", value=len(ref_asignadas))
col_m3.metric(label="Eventos en bitácora", value=len(historial))

st.markdown("")

tab1, tab2, tab3 = st.tabs([
    "Ficha, planos y refacciones",
    "Navegar y asignar refacción",
    "Bitácora de mantenimiento"
])

# ---------------------------------------------------------------------------
# Pestaña 1: Ficha, Archivos Múltiples y Resumen
# ---------------------------------------------------------------------------
with tab1:
    col_f1, col_f2 = st.columns([1.1, 0.9])

    with col_f1:
        encabezado_panel("Galería de planos, fotos y documentos del activo")

        if lista_archivos:
            aviso(f"Este equipo cuenta con {len(lista_archivos)} archivo(s) adjunto(s).", "ok")
            
            for arc in lista_archivos:
                nombre_arc = arc.get('nombre_archivo', 'Archivo')
                url_arc = arc.get('archivo_url')
                id_arc = arc.get('id')
                
                with st.container(border=True):
                    st.markdown(f"Archivo: **{nombre_arc}**")
                    
                    if any(url_arc.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                        st.image(url_arc, caption=nombre_arc, use_container_width=True)
                        st.markdown(f"[Abrir imagen en pestaña completa]({url_arc})")
                    elif url_arc.lower().endswith('.pdf'):
                        st.info("Archivo PDF disponible para visualización o descarga.")
                        st.markdown(f"[Hacer clic aquí para abrir el PDF en el navegador]({url_arc})")
                    else:
                        st.markdown(f"[Descargar archivo]({url_arc})")
                    
                    if st.button("Eliminar este archivo", key=f"del_arc_{id_arc}", type="secondary"):
                        try:
                            supabase.table("archivos_equipos").delete().eq("id", id_arc).execute()
                            st.success("Archivo eliminado.")
                            st.rerun()
                        except Exception as e:
                            aviso(f"Error al eliminar: {e}", "error", suelto=True)
        else:
            aviso("Este equipo no tiene planos o imágenes adjuntas.")

        with st.expander("Subir nuevo plano o foto (Múltiples archivos)"):
            archivo_subido = st.file_uploader("Selecciona imagen o PDF", type=["png", "jpg", "jpeg", "pdf"], key="multi_uploader")
            if st.button("Guardar archivo en el equipo"):
                if archivo_subido is not None:
                    try:
                        file_path = f"{codigo_activo_actual}/{archivo_subido.name}"

                        content_type = "application/pdf" if archivo_subido.name.lower().endswith('.pdf') else "image/jpeg"

                        supabase.storage.from_("Archivo equipos").upload(
                            file_path,
                            archivo_subido.getvalue(),
                            file_options={"upsert": "true", "content-type": content_type}
                        )

                        public_url = supabase.storage.from_("Archivo equipos").get_public_url(file_path)

                        supabase.table("archivos_equipos").insert({
                            "registro_id": id_equipo_actual,
                            "nombre_archivo": archivo_subido.name,
                            "archivo_url": public_url
                        }).execute()

                        st.success("Archivo subido y asociado correctamente.")
                        st.rerun()
                    except Exception as e:
                        aviso(f"Error al subir el archivo: {e}", "error", suelto=True)
                else:
                    aviso("Selecciona un archivo primero.", "warn", suelto=True)

    with col_f2:
        encabezado_panel("Últimas 3 refacciones ingresadas")
        if ref_asignadas:
            ref_ordenadas = sorted(ref_asignadas, key=lambda x: x.get('created_at', '') or '', reverse=True)[:3]
            datos_ref_recientes = []
            for item in ref_ordenadas:
                ref_detalles = item.get("refacciones", {})
                if ref_detalles:
                    datos_ref_recientes.append({
                        "Ítem": ref_detalles.get('ITEM'),
                        "Descripción": ref_detalles.get('DESCRIPCION'),
                        "Cant.": item.get("cantidad_requerida")
                    })
            if datos_ref_recientes:
                st.dataframe(datos_ref_recientes, use_container_width=True, hide_index=True)
            else:
                aviso("No hay registros recientes de refacciones.")
        else:
            aviso("No hay refacciones asociadas.")

        st.markdown("")

        encabezado_panel("Últimos 3 reportes de bitácora")
        if historial:
            historial_ultimos_3 = sorted(historial, key=lambda x: x.get('created_at', ''), reverse=True)[:3]
            datos_hist_recientes = []
            for evento in historial_ultimos_3:
                datos_hist_recientes.append({
                    "Fecha": evento.get('created_at', '')[:10],
                    "Tipo": evento.get('tipo_evento', 'General'),
                    "Detalle": evento.get('descripcion', '')
                })
            st.dataframe(datos_hist_recientes, use_container_width=True, hide_index=True)
        else:
            aviso("No hay eventos registrados en la bitácora.")

# ---------------------------------------------------------------------------
# Pestaña 2: Navegar refacciones asociadas y asignar nuevas (Con decimales)
# ---------------------------------------------------------------------------
with tab2:
    col_n1, col_n2 = st.columns([1.3, 0.7])

    with col_n1:
        encabezado_panel("Navegador de refacciones asociadas a este equipo")
        if ref_asignadas:
            datos_asociadas_nav = []
            opciones_desvincular = {}
            for item in ref_asignadas:
                ref_detalles = item.get("refacciones", {})
                if ref_detalles:
                    item_num = ref_detalles.get('ITEM')
                    desc = ref_detalles.get('DESCRIPCION')
                    
                    label_desc = f"Ítem {item_num} - {desc}"
                    opciones_desvincular[label_desc] = item.get("id")

                    datos_asociadas_nav.append({
                        "Ítem": item_num,
                        "Descripción": desc,
                        "Referencia": ref_detalles.get('REFERENCIA'),
                        "Cantidad Asignada": item.get("cantidad_requerida")
                    })
            
            df_asociadas = pd.DataFrame(datos_asociadas_nav)
            st.dataframe(df_asociadas, use_container_width=True, hide_index=True)

            with st.expander("Desvincular refacción del equipo"):
                id_relacion_a_borrar_label = st.selectbox("Selecciona refacción a retirar:", list(opciones_desvincular.keys()))
                id_relacion_a_borrar = opciones_desvincular[id_relacion_a_borrar_label]

                if st.button("Eliminar asociación", type="secondary"):
                    try:
                        supabase.table("equipo_refacciones").delete().eq("id", id_relacion_a_borrar).execute()
                        st.success("Desvinculado con éxito.")
                        st.rerun()
                    except Exception as e:
                        aviso(f"Error: {e}", "error", suelto=True)
        else:
            aviso("Este equipo aún no tiene refacciones asociadas.")

    with col_n2:
        encabezado_panel("Asignar nueva refacción")
        cat_ref_res = supabase.table("refacciones").select("*").execute()
        catalogo = cat_ref_res.data or []

        if catalogo:
            with st.form("form_asignar_ref_visual"):
                opciones_catalogo = {}
                for r in catalogo:
                    item_id = r.get('id')
                    item_num = r.get('ITEM', 'Sin Ítem')
                    desc = r.get('DESCRIPCION', 'Sin Descripción')
                    label = f"Ítem {item_num} - {desc}"
                    opciones_catalogo[label] = item_id

                ref_elegida_label = st.selectbox("Selecciona del catálogo:", list(opciones_catalogo.keys()))
                id_ref_elegida = opciones_catalogo[ref_elegida_label]
                
                cantidad_req = st.number_input("Cantidad requerida:", min_value=0.01, value=1.0, step=0.1, format="%.2f")

                if st.form_submit_button("Vincular refacción"):
                    try:
                        supabase.table("equipo_refacciones").insert({
                            "registro_id": id_equipo_actual,
                            "refaccion_id": id_ref_elegida,
                            "cantidad_requerida": cantidad_req
                        }).execute()
                        st.success("Refacción asignada con éxito.")
                        st.rerun()
                    except Exception as e:
                        aviso(f"Error al asignar: {e}", "error", suelto=True)
        else:
            aviso("El catálogo global está vacío.", "warn")

# ---------------------------------------------------------------------------
# Pestaña 3: Bitácora (Navegable y Exportable a Excel)
# ---------------------------------------------------------------------------
with tab3:
    col_h1, col_h2 = st.columns([1.3, 0.7])

    with col_h1:
        encabezado_panel("Navegador de bitácora e historial de eventos")
        
        historial_ordenado = sorted(historial, key=lambda x: x.get('created_at', ''), reverse=True)

        if historial_ordenado:
            datos_bitacora = []
            for evento in historial_ordenado:
                datos_bitacora.append({
                    "Fecha y Hora": evento.get('created_at', '')[:19],
                    "Tipo de Evento": evento.get('tipo_evento', 'General'),
                    "Descripción": evento.get('descripcion', ''),
                    "Técnico Responsable": evento.get('tecnico', 'No especificado')
                })
            
            df_bitacora = pd.DataFrame(datos_bitacora)
            
            st.dataframe(df_bitacora, use_container_width=True, hide_index=True)
            
            @st.cache_data
            def convertir_df_a_excel(df):
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Bitácora')
                processed_data = output.getvalue()
                return processed_data

            excel_data = convertir_df_a_excel(df_bitacora)
            
            st.download_button(
                label="Descargar Bitácora en Excel (.xlsx)",
                data=excel_data,
                file_name=f"Bitacora_{codigo_activo_actual}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            aviso("No hay eventos registrados en la bitácora de este equipo.")

    with col_h2:
        encabezado_panel("Registrar evento")
        with st.form("form_bitacora"):
            tipo_evento = st.selectbox("Tipo de evento", [
                "Mantenimiento Preventivo",
                "Mantenimiento Correctivo",
                "Falla Reportada",
                "Cambio de Componente",
                "Inspección"
            ])
            descripcion_evento = st.text_area("Detalle de lo realizado / suceso")
            nombre_tecnico = st.text_input("Técnico responsable")

            if st.form_submit_button("Guardar en la bitácora"):
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
                        aviso(f"Error: {e}", "error", suelto=True)
                else:
                    aviso("La descripción no puede estar vacía.", "warn", suelto=True)
