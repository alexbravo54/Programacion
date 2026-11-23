import base64
from datetime import datetime, time
from io import BytesIO
import re
import pandas as pd
import requests
import streamlit as str_app
import streamlit.components.v1 as components
from supabase import create_client

SUPABASE_URL = "https://tdhvesgqjowgzkwcsofy.supabase.co/"
SUPABASE_KEY = "sb_publishable_ePVH6D7O0L88kY48WMHGjA_CN2SsnHZ"

# ------------------------------------------------------------------
# CONFIGURACIÓN POWER AUTOMATE Y SHAREPOINT
# ------------------------------------------------------------------
POWER_AUTOMATE_UPLOAD_URL = (
    "https://575cd9ba20c1e27d907e387ee27e5f.e6.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/09/workflows/e7d0f97cc2944e03a231de69caf2f8d8/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=9Dwxi0TLZ86Ob7CFhkxDHJEPzeWnB3CeXXGV4y_NMDw"
)


def sanear_nombre_carpeta_sharepoint(texto: str) -> str:
    """Limpia caracteres especiales no permitidos en rutas de SharePoint."""
    limpio = re.sub(r'[\\/:*?"<>|#%{}~&]', " ", str(texto or ""))
    limpio = re.sub(r"\s+", " ", limpio).strip(" .")
    return limpio or "Sin_Nombre"


def subir_a_sharepoint_via_flow(
    codigo_activo: str,
    nombre_equipo: str,
    nombre_archivo: str,
    contenido_bytes: bytes,
    content_type: str,
) -> str:
    """Envía el archivo codificado en Base64 al flujo HTTP de Power Automate y retorna la URL."""
    payload = {
        "accion": "subir",
        "codigo_activo": sanear_nombre_carpeta_sharepoint(codigo_activo),
        "nombre_equipo": sanear_nombre_carpeta_sharepoint(nombre_equipo),
        "nombre_archivo": nombre_archivo,
        "content_type": content_type,
        "contenido_base64": base64.b64encode(contenido_bytes).decode("utf-8"),
    }
    resp = requests.post(POWER_AUTOMATE_UPLOAD_URL, json=payload, timeout=300)
    resp.raise_for_status()

    data = resp.json() if resp.text else {}
    url_sharepoint = (data.get("url") or "").strip()
    if not url_sharepoint:
        raise ValueError(
            "Power Automate no devolvió la URL del archivo en SharePoint."
        )

    return url_sharepoint


@str_app.cache_data(show_spinner=False)
def descargar_archivo_via_flow(
    codigo_activo: str,
    nombre_equipo: str,
    nombre_archivo: str,
    url_sharepoint: str,
) -> bytes:
    """Solicita al flujo de Power Automate el archivo en Base64 y retorna sus bytes."""
    payload = {
        "accion": "descargar",
        "codigo_activo": sanear_nombre_carpeta_sharepoint(codigo_activo),
        "nombre_equipo": sanear_nombre_carpeta_sharepoint(nombre_equipo),
        "nombre_archivo": nombre_archivo,
        "url": url_sharepoint,
    }
    resp = requests.post(POWER_AUTOMATE_UPLOAD_URL, json=payload, timeout=300)
    resp.raise_for_status()

    data = resp.json() if resp.text else {}
    b64 = data.get("contenido_base64")
    if not b64:
        raise ValueError(
            "Power Automate no devolvió 'contenido_base64' al descargar."
        )

    return base64.b64decode(b64)


def abrir_barra_lateral_js():
    """Intenta abrir la barra lateral de Streamlit si se encuentra colapsada."""
    components.html(
        """
        <script>
        (function() {
            const doc = window.parent.document;
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            const isExpanded = sidebar && sidebar.getAttribute('aria-expanded') === 'true';
            if (!isExpanded) {
                const expandBtn =
                    doc.querySelector('[data-testid="collapsedControl"] button') ||
                    doc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                    doc.querySelector('button[aria-label="Expand sidebar"]') ||
                    doc.querySelector('button[title="Expand sidebar"]');
                if (expandBtn) {
                    expandBtn.click();
                }
            }
        })();
        </script>
        """,
        height=0,
        width=0,
    )


@str_app.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()

str_app.set_page_config(
    page_title="Control de Equipos | Mantenimiento", layout="wide"
)

str_app.markdown(
    """
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

    .stApp { background: var(--bg); color: var(--txt); }
    .block-container { padding-top: 2rem; max-width: 1450px; }
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDeployButton"] { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    /* Mantener visible el control para reabrir la barra lateral */
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        opacity: 1 !important;
        color: var(--navy) !important;
    }

    p, span, label, div { color: var(--txt); }

    [data-testid="stSidebar"] { background: var(--navy); border-right: 1px solid var(--navy); }
    [data-testid="stSidebar"] label p, [data-testid="stSidebar"] span {
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

    .crumb { font-size: 12px; color: var(--txt-2); margin-bottom: 6px; }
    .titulo { font-size: 26px; font-weight: 500; color: var(--navy); margin: 0 0 4px 0; }
    .subtitulo { font-size: 13px; color: #3B465A; margin-bottom: 22px; }

    .foto-oficial-container img {
        max-height: 160px;
        object-fit: contain;
        border: 1px solid var(--line);
        background: #FFFFFF;
    }

    [data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid var(--line);
        border-top: 3px solid var(--navy); padding: 12px 14px;
    }
    [data-testid="stMetricLabel"] p { font-size: 12px; color: var(--txt-2); }
    [data-testid="stMetricValue"] { font-size: 22px; font-weight: 500; color: var(--navy); }

    div[data-baseweb="tab-list"] { gap: 28px; margin-bottom: 10px; }
    button[data-baseweb="tab"] p { font-size: 13px; color: var(--txt-2); }
    button[data-baseweb="tab"][aria-selected="true"] p { color: var(--navy); font-weight: 500; }
    div[data-baseweb="tab-highlight"] { background-color: var(--navy); height: 3px; }
    div[data-baseweb="tab-border"] { background-color: #CBD2DC; }

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

    div.stButton > button,
    div.stDownloadButton > button,
    div.stLinkButton > a,
    [data-testid="stFormSubmitButton"] > button,
    button[kind="secondary"],
    button[kind="primary"] {
        width: 100%; border-radius: 2px;
        background: var(--navy) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--navy) !important;
        font-size: 13px !important;
        text-decoration: none !important;
        white-space: nowrap !important;
    }
    div.stButton > button *,
    div.stDownloadButton > button *,
    div.stLinkButton > a *,
    [data-testid="stFormSubmitButton"] > button *,
    button[kind="secondary"] *,
    button[kind="primary"] * {
        color: #FFFFFF !important;
        white-space: nowrap !important;
    }
    div.stButton > button:hover,
    div.stDownloadButton > button:hover,
    div.stLinkButton > a:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: var(--navy-2) !important;
        border-color: var(--navy-2) !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    input, textarea {
        color: var(--txt) !important;
        background-color: #FFFFFF !important;
        -webkit-text-fill-color: var(--txt) !important;
    }

    div[data-baseweb="input"], div[data-baseweb="textarea"] { border-radius: 2px; }
    div[data-baseweb="select"] > div { border-radius: 2px; }
    [data-testid="stExpander"], [data-testid="stForm"] {
        background: #FFFFFF; border: 1px solid var(--line); border-radius: 0;
    }
    [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 0; }
    h3 { font-size: 15px !important; font-weight: 500 !important; color: var(--navy); margin-top: 0px !important; }

    /* Traducción de instrucciones del file_uploader */
    [data-testid="stFileUploaderDropzoneInstructions"] > div:last-child,
    [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        font-size: 0 !important;
        line-height: 0 !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"]::after {
        content: "PNG, JPG, PDF";
        font-size: 12px !important;
        line-height: 1.4 !important;
        color: var(--txt-2) !important;
        display: block;
        margin-top: 2px;
    }
</style>
""",
    unsafe_allow_html=True,
)


def aviso(texto, tipo="info", suelto=False):
    clases = f"aviso {tipo}" + (" suelto" if suelto else "")
    str_app.markdown(
        f'<div class="{clases}">{texto}</div>', unsafe_allow_html=True
    )


def encabezado_panel(texto):
    str_app.markdown(f'<div class="ph">{texto}</div>', unsafe_allow_html=True)


def cargar_todos_los_equipos():
    todos_los_datos = []
    chunk_size = 1000
    offset = 0
    while True:
        res = (
            supabase.table("equipos")
            .select("*")
            .range(offset, offset + chunk_size - 1)
            .execute()
        )
        datos_chunk = res.data or []
        todos_los_datos.extend(datos_chunk)
        if len(datos_chunk) < chunk_size:
            break
        offset += chunk_size
    return todos_los_datos


equipos = cargar_todos_los_equipos()

if not equipos:
    aviso(
        "No hay equipos registrados en la tabla 'equipos'.",
        "warn",
        suelto=True,
    )
    str_app.stop()

query_params = str_app.query_params
codigo_activo_en_url = query_params.get("equipo", None)

equipo_encontrado_por_qr = None
if codigo_activo_en_url is not None:
    equipo_encontrado_por_qr = next(
        (
            eq
            for eq in equipos
            if str(eq.get("Codigo de Activo", "")).strip()
            == str(codigo_activo_en_url).strip()
        ),
        None,
    )

str_app.sidebar.markdown(
    '<p class="sb-title">GESTIÓN DE ACTIVOS</p>'
    '<p class="sb-sub">Búsqueda y filtros</p>',
    unsafe_allow_html=True,
)

plantas_disponibles = ["Todas"] + sorted(
    list(
        set(
            str(eq.get("Planta", "Sin Planta"))
            for eq in equipos
            if eq.get("Planta")
        )
    )
)

planta_por_defecto = 0
if (
    equipo_encontrado_por_qr
    and equipo_encontrado_por_qr.get("Planta") in plantas_disponibles
):
    planta_por_defecto = plantas_disponibles.index(
        equipo_encontrado_por_qr.get("Planta")
    )

planta_seleccionada = str_app.sidebar.selectbox(
    "Planta", plantas_disponibles, index=planta_por_defecto
)

equipos_filtrados = equipos
if planta_seleccionada != "Todas":
    equipos_filtrados = [
        eq
        for eq in equipos_filtrados
        if str(eq.get("Planta", "Sin Planta")) == planta_seleccionada
    ]

lineas_disponibles = ["Todas"] + sorted(
    list(
        set(
            str(eq.get("Linea", "Sin Línea"))
            for eq in equipos_filtrados
            if eq.get("Linea")
        )
    )
)

linea_por_defecto = 0
if (
    equipo_encontrado_por_qr
    and equipo_encontrado_por_qr.get("Linea") in lineas_disponibles
):
    linea_por_defecto = lineas_disponibles.index(
        equipo_encontrado_por_qr.get("Linea")
    )

linea_seleccionada = str_app.sidebar.selectbox(
    "Línea", lineas_disponibles, index=linea_por_defecto
)

if linea_seleccionada != "Todas":
    equipos_filtrados = [
        eq
        for eq in equipos_filtrados
        if str(eq.get("Linea", "Sin Línea")) == linea_seleccionada
    ]

equipos_filtrados = sorted(
    equipos_filtrados, key=lambda x: str(x.get("Codigo de Activo", ""))
)

opciones_equipos = {}
indice_equipo_select = 0

for idx, eq in enumerate(equipos_filtrados):
    codigo = eq.get("Codigo de Activo", "Sin Código")
    desc = eq.get("Equipo") or eq.get("descripcion_equipo") or ""
    label = f"{codigo} - {desc}" if desc else codigo
    opciones_equipos[label] = eq["id"]

    if equipo_encontrado_por_qr and eq["id"] == equipo_encontrado_por_qr["id"]:
        indice_equipo_select = idx

if not opciones_equipos:
    with str_app.sidebar:
        aviso(
            "No hay equipos con los filtros seleccionados.",
            "warn",
            suelto=True,
        )
    str_app.stop()

equipo_seleccionado_label = str_app.sidebar.selectbox(
    "Equipo", list(opciones_equipos.keys()), index=indice_equipo_select
)
id_equipo_actual = opciones_equipos[equipo_seleccionado_label]

equipo_info = next(eq for eq in equipos if eq["id"] == id_equipo_actual)
codigo_activo_actual = equipo_info.get("Codigo de Activo", "N/A")
descripcion_actual = (
    equipo_info.get("Equipo") or equipo_info.get("descripcion_equipo") or ""
)

str_app.sidebar.markdown(
    f'<div class="sb-activo"><small>Activo seleccionado</small><b>{codigo_activo_actual}</b></div>',
    unsafe_allow_html=True,
)

# Botón superior para abrir/desplegar la barra lateral de plantas, líneas y equipos
col_btn_sb, _ = str_app.columns([0.24, 0.76])
with col_btn_sb:
    if str_app.button("Plantas, líneas y equipos", key="btn_abrir_sidebar"):
        abrir_barra_lateral_js()

col_head_txt, col_head_img = str_app.columns([0.85, 0.15])

with col_head_txt:
    str_app.markdown(
        f'<div class="crumb">Activos / Equipos / {codigo_activo_actual}</div>'
        f'<div class="titulo">Equipo {codigo_activo_actual}</div>',
        unsafe_allow_html=True,
    )
    partes_sub = []
    if descripcion_actual:
        partes_sub.append(str(descripcion_actual))
    partes_sub.append(f"Planta: {equipo_info.get('Planta', 'N/A')}")
    partes_sub.append(f"Línea: {equipo_info.get('Linea', 'N/A')}")
    str_app.markdown(
        f'<div class="subtitulo">{"  |  ".join(partes_sub)}</div>',
        unsafe_allow_html=True,
    )

with col_head_img:
    foto_url = equipo_info.get("foto_principal_url")
    str_app.markdown(
        '<div class="foto-oficial-container">', unsafe_allow_html=True
    )
    if foto_url:
        str_app.image(foto_url, caption="Foto oficial", use_container_width=True)
    else:
        with str_app.popover("Añadir foto"):
            str_app.markdown(
                "<b>Selecciona o sube la imagen</b>", unsafe_allow_html=True
            )
            foto_subida = str_app.file_uploader(
                "Selecciona imagen (PNG, JPG)",
                type=["png", "jpg", "jpeg"],
                key=f"sub_foto_principal_{id_equipo_actual}",
            )
            if foto_subida is not None and str_app.button(
                "Guardar foto oficial",
                key=f"btn_save_foto_{id_equipo_actual}",
            ):
                try:
                    file_path = f"{codigo_activo_actual}/foto_principal.jpg"
                    supabase.storage.from_("Archivo equipos").upload(
                        file_path,
                        foto_subida.getvalue(),
                        file_options={
                            "upsert": "true",
                            "content-type": "image/jpeg",
                        },
                    )
                    public_url = supabase.storage.from_(
                        "Archivo equipos"
                    ).get_public_url(file_path)
                    supabase.table("equipos").update(
                        {"foto_principal_url": public_url}
                    ).eq("id", id_equipo_actual).execute()
                    str_app.success("Foto oficial guardada con éxito.")
                    str_app.rerun()
                except Exception as e:
                    aviso(f"Error: {e}", "error", suelto=True)
    str_app.markdown("</div>", unsafe_allow_html=True)

query_ref_asig = (
    supabase.table("equipo_refacciones")
    .select(
        'id, cantidad_requerida, created_at, refacciones(id, "ITEM",'
        ' "DESCRIPCION", "REFERENCIA")'
    )
    .eq("registro_id", id_equipo_actual)
    .execute()
)
ref_asignadas = query_ref_asig.data or []

historial_res = (
    supabase.table("historial_equipos")
    .select("*")
    .eq("registro_id", id_equipo_actual)
    .execute()
)
historial = historial_res.data or []

archivos_res = (
    supabase.table("archivos_equipos")
    .select("*")
    .eq("registro_id", id_equipo_actual)
    .execute()
)
lista_archivos = archivos_res.data or []

col_m1, col_m2, col_m3 = str_app.columns(3)
col_m1.metric(label="Código de activo", value=codigo_activo_actual)
col_m2.metric(label="Refacciones vinculadas", value=len(ref_asignadas))
col_m3.metric(label="Eventos en bitácora", value=len(historial))

str_app.markdown("")

tab1, tab2, tab3 = str_app.tabs([
    "Ficha, planos y refacciones",
    "Navegar y asignar refacción",
    "Bitácora de mantenimiento",
])

if "file_uploader_key" not in str_app.session_state:
    str_app.session_state["file_uploader_key"] = 0

with tab1:
    col_f1, col_f2 = str_app.columns([1.1, 0.9])

    with col_f1:
        encabezado_panel("Planos, fotografías y documentos del activo")

        with str_app.popover("Subir nuevo archivo"):
            str_app.markdown(
                "<b>Selecciona archivo o PDF</b>", unsafe_allow_html=True
            )
            archivo_subido = str_app.file_uploader(
                "Selecciona imagen o PDF",
                type=["png", "jpg", "jpeg", "pdf"],
                key=(
                    "multi_uploader_"
                    f"{str_app.session_state['file_uploader_key']}"
                ),
            )

            if str_app.button("Guardar archivo en el equipo"):
                if archivo_subido is None:
                    aviso(
                        "Selecciona un archivo primero.",
                        "warn",
                        suelto=True,
                    )
                else:
                    try:
                        content_type = archivo_subido.type or (
                            "application/pdf"
                            if archivo_subido.name.lower().endswith(".pdf")
                            else "application/octet-stream"
                        )

                        url_sharepoint = subir_a_sharepoint_via_flow(
                            codigo_activo=codigo_activo_actual,
                            nombre_equipo=descripcion_actual
                            or f"Equipo_{codigo_activo_actual}",
                            nombre_archivo=archivo_subido.name,
                            contenido_bytes=archivo_subido.getvalue(),
                            content_type=content_type,
                        )

                        supabase.table("archivos_equipos").insert({
                            "registro_id": id_equipo_actual,
                            "nombre_archivo": archivo_subido.name,
                            "archivo_url": url_sharepoint,
                        }).execute()

                        descargar_archivo_via_flow.clear()
                        str_app.success(
                            "Archivo guardado en SharePoint y vinculado al"
                            " equipo."
                        )
                        str_app.session_state["file_uploader_key"] += 1
                        str_app.rerun()
                    except Exception as e:
                        aviso(
                            f"Error al enviar a SharePoint: {e}",
                            "error",
                            suelto=True,
                        )

        str_app.markdown(
            "<div style='margin-top: 10px;'></div>", unsafe_allow_html=True
        )

        if lista_archivos:
            for idx_arc, arc in enumerate(lista_archivos):
                nombre_arc = arc.get("nombre_archivo", "Archivo")
                url_arc = (arc.get("archivo_url") or "").strip()

                with str_app.container(border=True):
                    if url_arc:
                        col_info, col_abrir, col_desc = str_app.columns(
                            [1.55, 1.55, 0.9]
                        )
                        with col_info:
                            str_app.markdown(
                                f"Archivo: <b>{nombre_arc}</b>",
                                unsafe_allow_html=True,
                            )
                        with col_abrir:
                            str_app.link_button(
                                "Abrir en SharePoint",
                                url_arc,
                                use_container_width=True,
                            )
                        with col_desc:
                            try:
                                bytes_archivo = descargar_archivo_via_flow(
                                    codigo_activo=codigo_activo_actual,
                                    nombre_equipo=descripcion_actual
                                    or f"Equipo_{codigo_activo_actual}",
                                    nombre_archivo=nombre_arc,
                                    url_sharepoint=url_arc,
                                )
                                str_app.download_button(
                                    label="Descargar",
                                    data=bytes_archivo,
                                    file_name=nombre_arc,
                                    mime=(
                                        "application/pdf"
                                        if nombre_arc.lower().endswith(".pdf")
                                        else "application/octet-stream"
                                    ),
                                    key=f"dl_{id_equipo_actual}_{idx_arc}",
                                    use_container_width=True,
                                )
                            except Exception as e:
                                str_app.caption(f"No disponible: {e}")
                    else:
                        str_app.markdown(
                            f"Archivo: <b>{nombre_arc}</b> — <i>Sin enlace"
                            " disponible</i>",
                            unsafe_allow_html=True,
                        )
        else:
            aviso("Este equipo no tiene planos o imágenes adjuntas.")

    with col_f2:
        encabezado_panel("Últimas 3 refacciones ingresadas")
        if ref_asignadas:
            ref_ordenadas = sorted(
                ref_asignadas,
                key=lambda x: x.get("created_at", "") or "",
                reverse=True,
            )[:3]
            datos_ref_recientes = []
            for item in ref_ordenadas:
                ref_detalles = item.get("refacciones", {})
                if ref_detalles:
                    datos_ref_recientes.append({
                        "Ítem": ref_detalles.get("ITEM"),
                        "Descripción": ref_detalles.get("DESCRIPCION"),
                        "Cant.": item.get("cantidad_requerida"),
                    })
            if datos_ref_recientes:
                str_app.dataframe(
                    datos_ref_recientes,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                aviso("No hay registros recientes de refacciones.")
        else:
            aviso("No hay refacciones asociadas.")

        str_app.markdown("")

        encabezado_panel("Últimos 3 reportes de bitácora")
        if historial:
            historial_ultimos_3 = sorted(
                historial, key=lambda x: x.get("created_at", ""), reverse=True
            )[:3]
            datos_hist_recientes = []
            for evento in historial_ultimos_3:
                datos_hist_recientes.append({
                    "Fecha": evento.get("created_at", "")[:10],
                    "Tipo": evento.get("tipo_evento", "General"),
                    "Detalle": evento.get("descripcion", ""),
                })
            str_app.dataframe(
                datos_hist_recientes, use_container_width=True, hide_index=True
            )
        else:
            aviso("No hay eventos registrados en la bitácora.")

with tab2:
    encabezado_panel("Asignar nueva refacción al equipo")
    cat_ref_res = supabase.table("refacciones").select("*").execute()
    catalogo = cat_ref_res.data or []

    if catalogo:
        with str_app.form("form_asignar_ref_visual"):
            opciones_catalogo = {}
            for r in catalogo:
                item_id = r.get("id")
                item_num = str(r.get("ITEM", ""))
                desc = str(r.get("DESCRIPCION", "Sin Descripción"))
                ref_fab = str(r.get("REFERENCIA", ""))

                label = (
                    f"{desc}"
                    + (f"  |  Ref: {ref_fab}" if ref_fab else "")
                    + f"  [{item_num}]"
                )
                opciones_catalogo[label] = item_id

            col_s1, col_s2, col_s3 = str_app.columns([3.0, 0.8, 0.9])
            with col_s1:
                ref_elegida_label = str_app.selectbox(
                    "Seleccione refacción (puede escribir el código o"
                    " descripción para buscar):",
                    list(opciones_catalogo.keys()),
                )
                id_ref_elegida = opciones_catalogo[ref_elegida_label]
            with col_s2:
                cantidad_req = str_app.number_input(
                    "Cantidad:",
                    min_value=0.01,
                    value=1.0,
                    step=0.1,
                    format="%.2f",
                )
            with col_s3:
                str_app.markdown(
                    "<div style='height: 27px;'></div>", unsafe_allow_html=True
                )
                submit_vin = str_app.form_submit_button("Vincular")

            if submit_vin:
                try:
                    supabase.table("equipo_refacciones").insert({
                        "registro_id": id_equipo_actual,
                        "refaccion_id": str(id_ref_elegida),
                        "cantidad_requerida": cantidad_req,
                    }).execute()
                    str_app.success("Refacción asignada con éxito.")
                    str_app.rerun()
                except Exception as e:
                    aviso(f"Error al asignar: {e}", "error", suelto=True)
    else:
        aviso("El catálogo global está vacío.", "warn")

    str_app.markdown(
        "<div style='margin-top: 25px;'></div>", unsafe_allow_html=True
    )

    encabezado_panel("Navegador de refacciones asociadas a este equipo")
    if ref_asignadas:
        datos_asociadas_nav = []
        opciones_desvincular = {}
        for item in ref_asignadas:
            ref_detalles = item.get("refacciones", {})
            if ref_detalles:
                item_num = ref_detalles.get("ITEM")
                desc = ref_detalles.get("DESCRIPCION")

                label_desc = f"{desc} [{item_num}]"
                opciones_desvincular[label_desc] = item.get("id")

                datos_asociadas_nav.append({
                    "Ítem": item_num,
                    "Descripción": desc,
                    "Referencia": ref_detalles.get("REFERENCIA"),
                    "Cantidad Asignada": item.get("cantidad_requerida"),
                })

        df_asociadas = pd.DataFrame(datos_asociadas_nav)
        str_app.dataframe(
            df_asociadas, use_container_width=True, hide_index=True
        )

        with str_app.expander("Desvincular refacción del equipo"):
            col_d1, col_d2 = str_app.columns([2, 1])
            with col_d1:
                id_relacion_a_borrar_label = str_app.selectbox(
                    "Selecciona refacción a retirar:",
                    list(opciones_desvincular.keys()),
                )
                id_relacion_a_borrar = opciones_desvincular[
                    id_relacion_a_borrar_label
                ]
            with col_d2:
                str_app.markdown(
                    "<div style='height: 27px;'></div>", unsafe_allow_html=True
                )
                if str_app.button(
                    "Eliminar asociación", type="secondary"
                ):
                    try:
                        supabase.table("equipo_refacciones").delete().eq(
                            "id", str(id_relacion_a_borrar)
                        ).execute()
                        str_app.success("Desvinculado con éxito.")
                        str_app.rerun()
                    except Exception as e:
                        aviso(f"Error: {e}", "error", suelto=True)
    else:
        aviso("Este equipo aún no tiene refacciones asociadas.")

with tab3:
    encabezado_panel("Registrar evento")

    tipo_evento = str_app.selectbox(
        "Tipo de evento",
        [
            "Reportar falla",
            "Cambio de refaccion",
            "Inspección",
        ],
        key=f"tipo_evt_{id_equipo_actual}",
    )

    with str_app.form("form_bitacora"):
        descripcion_evento = str_app.text_area(
            "Detalle de lo realizado / suceso"
        )
        nombre_tecnico = str_app.text_input("Técnico responsable")

        col_i, col_f = str_app.columns(2)

        with col_i:
            str_app.markdown(
                "<b>Inicio de la actividad</b>", unsafe_allow_html=True
            )
            f_ini = str_app.date_input("Fecha inicio")

            c_txt1, c_ampm1 = str_app.columns([2, 1])
            with c_txt1:
                hora_ini_txt = str_app.text_input(
                    "Hora inicio (HH:MM)", value="12:00", key="h_txt_ini"
                )
            with c_ampm1:
                ampm_ini = str_app.selectbox(
                    "AM/PM", ["AM", "PM"], index=0, key="ampm_ini_sel"
                )

        with col_f:
            str_app.markdown(
                "<b>Fin de la actividad</b>", unsafe_allow_html=True
            )
            f_fin = str_app.date_input("Fecha fin")

            c_txt2, c_ampm2 = str_app.columns([2, 1])
            with c_txt2:
                hora_fin_txt = str_app.text_input(
                    "Hora fin (HH:MM)", value="01:00", key="h_txt_fin"
                )
            with c_ampm2:
                ampm_fin = str_app.selectbox(
                    "AM/PM", ["AM", "PM"], index=0, key="ampm_fin_sel"
                )

        def parsear_hora_12h(hora_str, ampm_str):
            try:
                partes = hora_str.strip().split(":")
                if len(partes) != 2:
                    return None
                h = int(partes[0])
                m = int(partes[1])

                if not (1 <= h <= 12) or not (0 <= m <= 59):
                    return None

                if ampm_str == "PM" and h < 12:
                    h += 12
                elif ampm_str == "AM" and h == 12:
                    h = 0
                return time(h, m, 0)
            except Exception:
                return None

        t_ini_24 = parsear_hora_12h(hora_ini_txt, ampm_ini)
        t_fin_24 = parsear_hora_12h(hora_fin_txt, ampm_fin)

        str_app.markdown(
            "<div style='margin-top: 10px;'></div>", unsafe_allow_html=True
        )

        if str_app.form_submit_button("Guardar en la bitácora"):
            if not descripcion_evento.strip():
                str_app.warning("La descripción no puede estar vacía.")
            elif t_ini_24 is None or t_fin_24 is None:
                str_app.error(
                    "Formato de hora inválido. Use el formato HH:MM (ejemplo:"
                    " 12:00 u 08:30) con horas de 1 a 12."
                )
            elif f_ini > f_fin:
                str_app.error(
                    "La fecha de inicio no puede ser posterior a la fecha fin."
                )
            else:
                dt_ini = datetime.combine(f_ini, t_ini_24)
                dt_fin = datetime.combine(f_fin, t_fin_24)

                if dt_ini >= dt_fin:
                    str_app.error(
                        "La hora de inicio no puede ser igual o posterior a la"
                        " hora fin en la misma fecha."
                    )
                else:
                    try:
                        diff_seconds = (dt_fin - dt_ini).total_seconds()
                        duracion_minutos = int(diff_seconds / 60)

                        fecha_inicio = (
                            f"{f_ini} {t_ini_24.strftime('%H:%M:%S')}"
                        )
                        fecha_fin = f"{f_fin} {t_fin_24.strftime('%H:%M:%S')}"

                        payload = {
                            "registro_id": id_equipo_actual,
                            "tipo_evento": tipo_evento,
                            "descripcion": descripcion_evento,
                            "tecnico": nombre_tecnico,
                            "fecha_inicio": fecha_inicio,
                            "fecha_fin": fecha_fin,
                            "duracion_minutos": duracion_minutos,
                        }

                        supabase.table("historial_equipos").insert(
                            payload
                        ).execute()
                        str_app.success("Guardado en la bitácora con éxito.")
                        str_app.rerun()
                    except Exception as e:
                        aviso(f"Error: {e}", "error", suelto=True)

    str_app.markdown(
        "<div style='margin-top: 30px;'></div>", unsafe_allow_html=True
    )
    encabezado_panel("Navegador de bitácora e historial de eventos")

    historial_ordenado = sorted(
        historial, key=lambda x: x.get("created_at", ""), reverse=True
    )

    if historial_ordenado:
        datos_bitacora = []
        for evento in historial_ordenado:
            datos_bitacora.append({
                "Fecha y Hora": evento.get("created_at", "")[:19],
                "Tipo de Evento": evento.get("tipo_evento", "General"),
                "Descripción": evento.get("descripcion", ""),
                "Técnico Responsable": evento.get("tecnico", "No especificado"),
                "F. Inicio": evento.get("fecha_inicio", ""),
                "F. Fin": evento.get("fecha_fin", ""),
                "Duración (Min)": evento.get("duracion_minutos", ""),
            })

        df_bitacora = pd.DataFrame(datos_bitacora)

        str_app.dataframe(
            df_bitacora, use_container_width=True, hide_index=True
        )

        @str_app.cache_data
        def convertir_df_a_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Bitácora")
            return output.getvalue()

        excel_data = convertir_df_a_excel(df_bitacora)

        str_app.download_button(
            label="Descargar Bitácora en Excel (.xlsx)",
            data=excel_data,
            file_name=f"Bitacora_{codigo_activo_actual}.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
    else:
        aviso("No hay eventos registrados en la bitácora de este equipo.")
