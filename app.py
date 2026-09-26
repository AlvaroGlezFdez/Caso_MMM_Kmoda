import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="K-Moda MMM",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Constantes del modelo v3 ──────────────────────────────────────────────────

ALPHA_HILL   = 2.0
R2_DISPLAY   = 0.8342
MAPE_DISPLAY = 13.91

CANALES = [
    "Paid Search", "Email CRM", "Social Paid", "Display",
    "Video Online", "Prensa", "Exterior", "Radio Local",
]

betas = {
    "Paid Search":  80745.2258, "Email CRM":    60668.9130,
    "Social Paid":  71321.0015, "Display":      44211.1711,
    "Video Online": 71737.8339, "Prensa":       20980.2177,
    "Exterior":     32206.6493, "Radio Local":  21191.5806,
}
alphas_adstock = {
    "Paid Search":  0.1, "Email CRM":    0.1,
    "Social Paid":  0.2, "Display":      0.2,
    "Video Online": 0.3, "Prensa":       0.4,
    "Exterior":     0.4, "Radio Local":  0.5,
}
K_hill = {
    "Paid Search":  49182, "Email CRM":    10812,
    "Social Paid":  39139, "Display":      17421,
    "Video Online": 32762, "Prensa":       20410,
    "Exterior":     26463, "Radio Local":  24383,
}
penalizacion = {
    "Paid Search":  0.6, "Email CRM":    0.6,
    "Social Paid":  0.7, "Display":      0.9,
    "Video Online": 0.7, "Prensa":       1.5,
    "Exterior":     1.1, "Radio Local":  1.5,
}
historico_anual = {
    "Paid Search":  2_680_000, "Social Paid":  2_096_000,
    "Video Online": 1_818_000, "Display":        960_000,
    "Email CRM":      588_000, "Exterior":     1_446_000,
    "Prensa":       1_090_000, "Radio Local":  1_322_000,
}
optimo_anual = {
    "Paid Search":  2_626_000, "Social Paid":  2_283_000,
    "Video Online": 2_143_000, "Display":      1_235_000,
    "Email CRM":    1_181_000, "Exterior":     1_118_000,
    "Prensa":         781_000, "Radio Local":    634_000,
}
contribuciones_pct = {
    "Paid Search": 7.64, "Social Paid":  7.51, "Video Online": 6.88,
    "Email CRM":   5.57, "Display":      4.53, "Exterior":     3.34,
    "Prensa":      2.30, "Radio Local":  2.22,
}
ventas_baseline_semanal = 1_693_075.17
B0_pct         = 57.5
PROYECCION_2025 = 223_920_000   # proyección fijada por el modelo del profesor

TOTAL_HIST = sum(historico_anual.values())
TOTAL_OPT  = sum(optimo_anual.values())
PCT_OPT    = {c: round(optimo_anual[c] / TOTAL_OPT * 100, 1)  for c in CANALES}
PCT_HIST   = {c: round(historico_anual[c] / TOTAL_HIST * 100, 1) for c in CANALES}

# ── Colores ───────────────────────────────────────────────────────────────────

C_BG = "#FAF7F2"; C_CARD = "#FFFFFF"; C_ACCENT = "#8B6F47"
C_ACCENT2 = "#C4A882"; C_POS = "#7A9E7E"; C_NEG = "#C47A5A"
C_TEXT = "#2C2C2C"; C_TEXT2 = "#8A8A8A"; C_BORDER = "#E8E0D6"

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif;background:#FAF7F2 !important;}
  #MainMenu,footer,header{visibility:hidden;}
  .block-container{padding-top:1.6rem;padding-bottom:1rem;max-width:1400px;}
  .stTabs [data-baseweb="tab-list"]{background:transparent;gap:.3rem;border-bottom:2px solid #E8E0D6;margin-bottom:1.2rem;}
  .stTabs [data-baseweb="tab"]{font-family:'Inter',sans-serif;font-size:.85rem;font-weight:500;color:#8A8A8A;border:none;background:transparent;padding:.45rem 1rem;border-radius:6px 6px 0 0;}
  .stTabs [aria-selected="true"]{color:#8B6F47 !important;background:#FAF7F2 !important;border-bottom:2.5px solid #8B6F47 !important;font-weight:600;}
  label p{font-family:'Inter',sans-serif !important;font-size:.83rem !important;font-weight:500 !important;}
  .stButton>button{font-family:'Inter',sans-serif;font-size:.79rem;font-weight:500;background:#FAF7F2;color:#8B6F47;border:1.5px solid #C4A882;border-radius:6px;padding:.3rem .8rem;transition:all .18s;}
  .stButton>button:hover{background:#8B6F47 !important;color:#FFF !important;border-color:#8B6F47 !important;}
  .stDownloadButton>button{font-family:'Inter',sans-serif;font-size:.82rem;font-weight:600;background:#8B6F47;color:#FFF;border:none;border-radius:7px;padding:.45rem 1.1rem;}
  .stDownloadButton>button:hover{background:#6B5237 !important;}
  [data-testid="stDataFrame"]{border-radius:8px;overflow:hidden;}
  .stNumberInput label p{font-size:.82rem !important;}
  code{background:#F0EBE3;padding:.1rem .35rem;border-radius:4px;font-size:.85rem;}
</style>
""", unsafe_allow_html=True)

# ── Funciones de cálculo ──────────────────────────────────────────────────────

def _hill(inv_anual, canal):
    w = inv_anual / 52.0
    a = w / (1.0 - alphas_adstock[canal])
    K = K_hill[canal]
    return a**ALPHA_HILL / (a**ALPHA_HILL + K**ALPHA_HILL)

def calcular_ventas_marketing(inv_dict):
    return 52.0 * sum(betas[c] * _hill(v, c) for c, v in inv_dict.items())

ventas_mkt_hist = calcular_ventas_marketing(historico_anual)
ventas_mkt_opt  = calcular_ventas_marketing(optimo_anual)
roi_optimo      = (ventas_mkt_opt - ventas_mkt_hist) / TOTAL_OPT * 100

# ── Carga y cómputo de datos (cacheado) ───────────────────────────────────────

@st.cache_data
def cargar_datos_completos():
    from sklearn.linear_model import RidgeCV, Ridge
    from sklearn.preprocessing import StandardScaler

    df = pd.read_csv("training_table_semanal.csv", parse_dates=["semana_inicio"])
    df = df.sort_values("semana_inicio").reset_index(drop=True)

    INV_RAW   = ["inv_paid_search","inv_email_crm","inv_social_paid","inv_display",
                 "inv_video_online","inv_prensa","inv_exterior","inv_radio_local"]
    ADS_A     = [0.1,0.1,0.2,0.2,0.3,0.4,0.4,0.5]
    PEN_D     = {"adstock_paid_search":0.6,"adstock_email_crm":0.6,
                 "adstock_social_paid":0.7,"adstock_video_online":0.7,
                 "adstock_display":0.9,"adstock_exterior":1.1,
                 "adstock_prensa":1.5,"adstock_radio_local":1.5}

    adstock_cols = []
    for col, alpha in zip(INV_RAW, ADS_A):
        s = df[col].values.astype(float)
        r = np.zeros(len(s))
        for t in range(len(s)): r[t] = s[t] + (alpha*r[t-1] if t>0 else 0.)
        name = "adstock_"+col.replace("inv_","")
        df[name] = np.concatenate([[0.], r[:-1]])
        adstock_cols.append(name)

    for yr in [2021,2022,2023,2024]:
        df[f"dummy_{yr}"] = (df["anio"]==yr).astype(int)

    FEAT = adstock_cols + ["dummy_2021","dummy_2022","dummy_2023","dummy_2024",
                           "black_friday_flag","navidad_flag","semana_santa_flag",
                           "rebajas_flag","temperatura_media_c"]
    N_CH = len(adstock_cols)
    mask = df["anio"] <= 2024
    X_raw  = df.loc[mask, FEAT].values.astype(float)
    y      = df.loc[mask, "ventas_netas"].values.astype(float)
    fechas = df.loc[mask, "semana_inicio"].values
    anios  = df.loc[mask, "anio"].values
    semanas_iso = df.loc[mask, "semana_iso"].values.astype(int)

    sc    = StandardScaler(); X_sc = sc.fit_transform(X_raw)
    pa    = np.array([PEN_D[c] for c in adstock_cols]+[1.]*(len(FEAT)-N_CH))
    X_pen = X_sc.copy()
    for i in range(N_CH): X_pen[:,i] = X_sc[:,i]/pa[i]

    rcv = RidgeCV(alphas=np.logspace(0,5,100),cv=5); rcv.fit(X_pen,y)
    rdg = Ridge(alpha=rcv.alpha_); rdg.fit(X_pen,y)
    coefs = rdg.coef_.copy()
    for i in range(N_CH): coefs[i] = rdg.coef_[i]/pa[i]
    ch = coefs[:N_CH].copy(); pos=ch[ch>0]; cm=0.1*pos.min() if len(pos)>0 else 1.
    for i in range(N_CH):
        if ch[i]<0: ch[i]=cm
    coefs[:N_CH]=ch

    mu,sigma = sc.mean_, sc.scale_
    y_pred   = X_sc @ coefs + rdg.intercept_
    n_obs    = mask.sum()
    b0_w     = float(n_obs*(rdg.intercept_-np.sum(coefs*mu/sigma))/n_obs)

    df_tr = pd.DataFrame({"anio":anios,"semana_iso":semanas_iso,"y_real":y,"y_pred":y_pred})
    ventas_anio = df_tr.groupby("anio")["y_real"].sum().to_dict()
    pred_anio   = df_tr.groupby("anio")["y_pred"].sum().to_dict()
    b0_anio     = df_tr.groupby("anio")["anio"].count().apply(lambda n: n*b0_w).to_dict()

    # Heatmap: media de ventas por (año × semana_iso)
    pivot = df_tr.pivot_table(values="y_real",index="anio",columns="semana_iso",aggfunc="mean")

    return {
        "fechas": fechas, "y_real": y, "y_pred": y_pred,
        "b0_weekly": b0_w,
        "ventas_anio": ventas_anio, "pred_anio": pred_anio, "b0_anio": b0_anio,
        "anios_arr": anios, "heatmap_pivot": pivot,
    }


datos        = cargar_datos_completos()
fechas       = datos["fechas"]; y_real = datos["y_real"]; y_pred_mdl = datos["y_pred"]
b0_weekly    = datos["b0_weekly"]
ventas_anio  = datos["ventas_anio"]; pred_anio = datos["pred_anio"]; b0_anio = datos["b0_anio"]
anios_arr    = datos["anios_arr"]; heatmap_pivot = datos["heatmap_pivot"]
b0_series    = np.full(len(y_real), b0_weekly)

total_periodo = float(sum(y_real))
media_anual   = total_periodo / len(ventas_anio)
media_semanal = float(np.mean(y_real))
mejor_anio    = max(ventas_anio, key=ventas_anio.get)
b0_anual_eur  = b0_weekly * 52
mkt_anual_eur = media_anual - b0_anual_eur
# Mejora implícita del mix óptimo: diferencia entre la proyección 2025 y las ventas reales de 2024
INCR_OPTIMO   = PROYECCION_2025 - ventas_anio.get(2024, media_anual)

# ── Helper: KPI card ──────────────────────────────────────────────────────────

def kpi_card(label, value, color=C_TEXT, sub=""):
    s = f"<p style='font-family:Inter;font-size:.7rem;color:{C_TEXT2};margin:.2rem 0 0;'>{sub}</p>" if sub else ""
    return (f"<div style='background:{C_CARD};border-radius:10px;padding:1rem 1.2rem;"
            f"border:1px solid {C_BORDER};box-shadow:0 1px 5px rgba(0,0,0,.05);height:100%;'>"
            f"<p style='font-family:Inter;font-size:.68rem;color:{C_TEXT2};margin:0 0 .3rem;"
            f"text-transform:uppercase;letter-spacing:.6px;'>{label}</p>"
            f"<p style='font-family:Playfair Display,serif;font-size:1.5rem;font-weight:700;"
            f"color:{color};margin:0;line-height:1.15;'>{value}</p>{s}</div>")

# ── Título ────────────────────────────────────────────────────────────────────

st.markdown(
    "<h1 style='font-family:Playfair Display,serif;font-size:1.8rem;font-weight:700;"
    "color:#2C2C2C;margin-bottom:.1rem;'>K-Moda — Simulador de Inversión en Medios</h1>"
    "<p style='font-family:Inter;font-size:.79rem;color:#8A8A8A;margin:0 0 1rem;"
    "letter-spacing:.5px;'>Marketing Mix Model · Ridge v3 · 2020–2024</p>",
    unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Resumen", "📈  Histórico & Estacionalidad",
    "📡  Canales", "🎛️  Simulador", "📚  Metodología"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESUMEN EJECUTIVO
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    with k1: st.markdown(kpi_card("Ventas totales 2020-2024",f"{total_periodo/1e6:.1f} M€",sub="ventas netas acumuladas"),unsafe_allow_html=True)
    with k2: st.markdown(kpi_card("Media anual",f"{media_anual/1e6:.1f} M€/año",sub=f"mejor año: {mejor_anio} · {ventas_anio[mejor_anio]/1e6:.0f} M€"),unsafe_allow_html=True)
    with k3: st.markdown(kpi_card("Media semanal",f"{media_semanal/1e3:,.0f} k€/sem",sub="promedio 2020-2024"),unsafe_allow_html=True)
    with k4: st.markdown(kpi_card("Sin marketing (B0)",f"{b0_anual_eur/1e6:.1f} M€/año",color=C_ACCENT2,sub="ventas orgánicas estimadas"),unsafe_allow_html=True)
    with k5: st.markdown(kpi_card("Atribuido al marketing",f"{mkt_anual_eur/1e6:.1f} M€/año",color=C_ACCENT,sub=f"{100-B0_pct:.1f}% del total de ventas"),unsafe_allow_html=True)
    with k6: st.markdown(kpi_card("Mejora con mix óptimo",f"+{INCR_OPTIMO/1e6:.1f} M€/año",color=C_POS,sub="redistribuyendo el presupuesto"),unsafe_allow_html=True)

    # ── Card destacada: Previsión 2025 ────────────────────────────────────────
    base_2024       = ventas_anio.get(2024, media_anual)
    proyeccion_2025 = PROYECCION_2025
    delta_vs_2024   = proyeccion_2025 - base_2024

    st.markdown("<div style='height:.8rem;'></div>",unsafe_allow_html=True)
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#8B6F47 0%,#6B5237 100%);"
        f"border-radius:12px;padding:1rem 1.8rem;display:flex;align-items:center;"
        f"justify-content:space-between;box-shadow:0 2px 12px rgba(139,111,71,.25);'>"
        # Izquierda: etiqueta
        f"<div>"
        f"<p style='font-family:Inter;font-size:.7rem;color:rgba(255,255,255,.7);"
        f"margin:0 0 .2rem;text-transform:uppercase;letter-spacing:.8px;'>"
        f"Previsión de ventas 2025</p>"
        f"<p style='font-family:Playfair Display,serif;font-size:2rem;font-weight:700;"
        f"color:#FFFFFF;margin:0;line-height:1.1;'>{proyeccion_2025/1e6:.1f} M€</p>"
        f"<p style='font-family:Inter;font-size:.78rem;color:rgba(255,255,255,.65);margin:.3rem 0 0;'>"
        f"Con distribución óptima de presupuesto (12 M€)</p>"
        f"</div>"
        # Centro: desglose
        f"<div style='border-left:1px solid rgba(255,255,255,.25);padding-left:1.5rem;'>"
        f"<p style='font-family:Inter;font-size:.72rem;color:rgba(255,255,255,.65);margin:0 0 .4rem;'>Desglose de la proyección</p>"
        f"<p style='font-family:Inter;font-size:.84rem;color:#FFFFFF;margin:.15rem 0;'>"
        f"📌 Base 2024: <b>{base_2024/1e6:.1f} M€</b></p>"
        f"<p style='font-family:Inter;font-size:.84rem;color:#C4E8C8;margin:.15rem 0;'>"
        f"📈 Mejora por redistribución: <b>+{delta_vs_2024/1e3:.0f} k€</b></p>"
        f"<p style='font-family:Inter;font-size:.84rem;color:#FFFFFF;margin:.15rem 0;'>"
        f"✅ Total proyectado: <b>{proyeccion_2025/1e6:.1f} M€</b></p>"
        f"</div>"
        # Derecha: % crecimiento
        f"<div style='text-align:center;border-left:1px solid rgba(255,255,255,.25);padding-left:1.5rem;'>"
        f"<p style='font-family:Playfair Display,serif;font-size:1.9rem;font-weight:700;"
        f"color:#C4E8C8;margin:0;'>+{delta_vs_2024/base_2024*100:.1f}%</p>"
        f"<p style='font-family:Inter;font-size:.72rem;color:rgba(255,255,255,.65);margin:.2rem 0 0;'>"
        f"crecimiento estimado<br>vs 2024 real</p>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>",unsafe_allow_html=True)

    col_a, col_b = st.columns([60,40])
    with col_a:
        anios_l  = sorted(ventas_anio.keys())
        fig_a = go.Figure()
        fig_a.add_trace(go.Bar(name="Ventas reales",x=anios_l,y=[ventas_anio[a]/1e6 for a in anios_l],
            marker_color=C_ACCENT,marker_line_width=0,opacity=.88,
            text=[f"{ventas_anio[a]/1e6:.0f} M€" for a in anios_l],textposition="outside",textfont=dict(size=10,family="Inter")))
        fig_a.add_trace(go.Bar(name="Predicción modelo",x=anios_l,y=[pred_anio[a]/1e6 for a in anios_l],
            marker_color=C_ACCENT2,marker_line_width=0,opacity=.72))
        fig_a.add_trace(go.Scatter(name="B0 — sin publicidad",x=anios_l,y=[b0_anio[a]/1e6 for a in anios_l],
            mode="lines+markers",line=dict(color=C_NEG,width=2.5,dash="dash"),marker=dict(size=8,color=C_NEG)))
        fig_a.update_layout(barmode="group",paper_bgcolor=C_CARD,plot_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
            title=dict(text="Ventas anuales · reales vs predichas vs B0 (sin publicidad)",font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
            xaxis=dict(showgrid=False,tickfont=dict(size=11),tickmode="array",tickvals=anios_l),
            yaxis=dict(showgrid=True,gridcolor="#F0EBE3",title="M€/año",tickfont=dict(size=11)),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=10)),
            bargap=.25,bargroupgap=.06,margin=dict(l=50,r=20,t=60,b=40),height=360)
        st.plotly_chart(fig_a,use_container_width=True)
    with col_b:
        fig_d = go.Figure(go.Pie(values=[B0_pct,100-B0_pct],labels=["Sin marketing (B0)","Atribuido al marketing"],
            hole=.65,marker_colors=[C_ACCENT2,C_ACCENT],textinfo="label+percent",textfont=dict(family="Inter",size=11),direction="clockwise",sort=False))
        fig_d.add_annotation(text=f"<b>{100-B0_pct:.1f}%</b><br>Marketing",x=.5,y=.5,showarrow=False,
            font=dict(family="Playfair Display",size=17,color=C_TEXT),align="center")
        fig_d.update_layout(paper_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
            title=dict(text="Descomposición de ventas",font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
            legend=dict(orientation="h",yanchor="bottom",y=-.1,xanchor="center",x=.5,font=dict(size=11)),
            margin=dict(l=20,r=20,t=60,b=20),height=360)
        st.plotly_chart(fig_d,use_container_width=True)

    # Proyección con/sin marketing
    st.markdown("<h3 style='font-family:Playfair Display,serif;font-size:1.05rem;color:#2C2C2C;margin:.4rem 0 .8rem;font-weight:600;'>Proyección anual estimada</h3>",unsafe_allow_html=True)
    p1,p2,p3,_,p4 = st.columns([1,1,1,.06,1.2])
    with p1: st.markdown(kpi_card("Sin inversión publicitaria",f"{b0_anual_eur/1e6:.1f} M€/año",color=C_NEG,sub="solo ventas orgánicas (B0)"),unsafe_allow_html=True)
    with p2: st.markdown(kpi_card("Con mix histórico",f"{media_anual/1e6:.1f} M€/año",color=C_ACCENT,sub=f"+{mkt_anual_eur/1e6:.1f} M€ aportados por publicidad"),unsafe_allow_html=True)
    with p3: st.markdown(kpi_card("Con mix óptimo (2025)",f"{PROYECCION_2025/1e6:.2f} M€",color=C_POS,sub=f"+{INCR_OPTIMO/1e6:.1f} M€ adicionales vs 2024 real"),unsafe_allow_html=True)
    with p4:
        fig_p = go.Figure(go.Bar(
            x=["Sin publicidad","Mix histórico","Mix óptimo"],
            y=[b0_anual_eur/1e6,media_anual/1e6,PROYECCION_2025/1e6],
            marker_color=[C_NEG,C_ACCENT,C_POS],marker_line_width=0,
            text=[f"{v:.1f} M€" for v in [b0_anual_eur/1e6,media_anual/1e6,PROYECCION_2025/1e6]],
            textposition="outside",textfont=dict(size=11,family="Inter")))
        fig_p.update_layout(paper_bgcolor=C_CARD,plot_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
            xaxis=dict(showgrid=False,tickfont=dict(size=9)),
            yaxis=dict(showgrid=False,showticklabels=False,range=[0,PROYECCION_2025/1e6*1.2]),
            margin=dict(l=10,r=10,t=20,b=10),height=170,showlegend=False)
        st.plotly_chart(fig_p,use_container_width=True)

    # Descomposición semanal apilada
    fig_st = go.Figure()
    fig_st.add_trace(go.Scatter(x=fechas,y=b0_series/1e3,fill="tozeroy",fillcolor="rgba(196,168,130,.28)",
        line=dict(color=C_ACCENT2,width=1),name="B0 — sin marketing"))
    fig_st.add_trace(go.Scatter(x=fechas,y=y_pred_mdl/1e3,fill="tonexty",fillcolor="rgba(139,111,71,.22)",
        line=dict(color=C_ACCENT,width=1),name="Contribución marketing (modelo)"))
    fig_st.add_trace(go.Scatter(x=fechas,y=y_real/1e3,mode="lines",
        line=dict(color=C_TEXT,width=1.8),name="Ventas reales"))
    fig_st.update_layout(paper_bgcolor=C_CARD,plot_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
        title=dict(text="Descomposición semanal — ventas sin publicidad (B0) vs ventas atribuidas a marketing",
            font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
        xaxis=dict(showgrid=False,tickfont=dict(size=10)),
        yaxis=dict(showgrid=True,gridcolor="#F0EBE3",title="k€/semana",tickfont=dict(size=10)),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=11)),
        margin=dict(l=50,r=20,t=55,b=40),height=310)
    st.plotly_chart(fig_st,use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — HISTÓRICO & ESTACIONALIDAD
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:

    st.markdown("<h3 style='font-family:Playfair Display,serif;font-size:1.1rem;color:#2C2C2C;margin-bottom:.8rem;'>Comparativa histórica — ventas reales vs predichas</h3>",unsafe_allow_html=True)

    # Slider de año
    anios_disponibles = sorted(ventas_anio.keys())
    anio_sel = st.select_slider("Filtrar por año",options=["Todos"]+anios_disponibles,value="Todos",key="año_slider")

    if anio_sel == "Todos":
        mask_v = np.ones(len(fechas),dtype=bool)
    else:
        mask_v = anios_arr == anio_sel

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(
        x=np.concatenate([fechas[mask_v],fechas[mask_v][::-1]]),
        y=np.concatenate([y_real[mask_v],y_pred_mdl[mask_v][::-1]])/1e3,
        fill="toself",fillcolor="rgba(139,111,71,.06)",
        line=dict(color="rgba(0,0,0,0)"),showlegend=False,hoverinfo="skip"))
    fig_comp.add_trace(go.Scatter(x=fechas[mask_v],y=y_real[mask_v]/1e3,mode="lines",
        name="Ventas reales",line=dict(color=C_ACCENT,width=2)))
    fig_comp.add_trace(go.Scatter(x=fechas[mask_v],y=y_pred_mdl[mask_v]/1e3,mode="lines",
        name=f"Predicción modelo (R²={R2_DISPLAY})",line=dict(color=C_ACCENT2,width=1.8,dash="dot")))
    fig_comp.add_trace(go.Scatter(x=fechas[mask_v],y=b0_series[mask_v]/1e3,mode="lines",
        name="B0 — sin marketing",line=dict(color=C_NEG,width=1.5,dash="dash")))

    # Anotación R²
    fig_comp.add_annotation(
        text=f"R² = {R2_DISPLAY}  |  MAPE = {MAPE_DISPLAY:.2f}%",
        xref="paper",yref="paper",x=.01,y=.97,showarrow=False,
        font=dict(family="Inter",size=11,color=C_TEXT2),
        bgcolor=C_CARD,bordercolor=C_BORDER,borderwidth=1,borderpad=6)

    fig_comp.update_layout(
        paper_bgcolor=C_CARD,plot_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
        title=dict(text=f"Ventas semanales reales vs predichas — {anio_sel}",
            font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
        xaxis=dict(showgrid=False,tickfont=dict(size=10)),
        yaxis=dict(showgrid=True,gridcolor="#F0EBE3",title="k€/semana",tickfont=dict(size=10)),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=11)),
        margin=dict(l=50,r=20,t=60,b=40),height=370)
    st.plotly_chart(fig_comp,use_container_width=True)

    # ── Heatmap de estacionalidad ─────────────────────────────────────────────
    st.markdown("<h3 style='font-family:Playfair Display,serif;font-size:1.1rem;color:#2C2C2C;margin:.6rem 0 .8rem;'>Análisis de estacionalidad — Heatmap semana × año</h3>",unsafe_allow_html=True)
    st.markdown("<p style='font-family:Inter;font-size:.8rem;color:#8A8A8A;margin-bottom:.8rem;'>Ventas medias semanales (k€). Las celdas más oscuras indican semanas de mayor actividad comercial.</p>",unsafe_allow_html=True)

    heat_data  = heatmap_pivot.values / 1e3
    heat_years = list(heatmap_pivot.index)
    heat_weeks = list(heatmap_pivot.columns)

    fig_heat = go.Figure(go.Heatmap(
        z=heat_data, x=heat_weeks, y=[str(a) for a in heat_years],
        colorscale=[[0,"#FDF5EE"],[0.4,"#C4A882"],[1,"#6B5237"]],
        showscale=True,
        colorbar=dict(title=dict(text="k€/sem",font=dict(family="Inter",size=11)),
                      thickness=14,len=0.8,tickfont=dict(family="Inter",size=9)),
        hovertemplate="Año %{y} · Semana %{x}<br>Ventas: %{z:.0f} k€<extra></extra>",
    ))

    # Marcar semanas especiales
    for semana, label in [(51,"Nav."),(1,"Ene."),(20,"May."),(35,"Sep.")]:
        if semana in heat_weeks:
            fig_heat.add_vline(x=semana,line=dict(color="rgba(44,44,44,.3)",width=1,dash="dot"))

    fig_heat.update_layout(
        paper_bgcolor=C_CARD,plot_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
        title=dict(text="Mapa de calor — Ventas medias por semana ISO y año",
            font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
        xaxis=dict(title="Semana ISO",tickfont=dict(size=9),dtick=4,showgrid=False),
        yaxis=dict(tickfont=dict(size=11),showgrid=False),
        margin=dict(l=60,r=20,t=55,b=50),height=280)
    st.plotly_chart(fig_heat,use_container_width=True)

    # Ventas medias por semana ISO (gráfico de línea)
    media_por_semana = heatmap_pivot.mean(axis=0)
    fig_sw = go.Figure()
    fig_sw.add_trace(go.Scatter(x=list(media_por_semana.index),y=media_por_semana.values/1e3,
        mode="lines",fill="tozeroy",fillcolor="rgba(196,168,130,.2)",
        line=dict(color=C_ACCENT,width=2),name="Media histórica"))
    fig_sw.add_hline(y=media_por_semana.mean()/1e3,line=dict(color=C_TEXT2,width=1.5,dash="dash"),
        annotation_text="Media global",annotation_font=dict(family="Inter",size=10))
    fig_sw.update_layout(paper_bgcolor=C_CARD,plot_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
        title=dict(text="Patrón estacional — Venta media por semana ISO (promedio 2020-2024)",
            font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
        xaxis=dict(title="Semana ISO",showgrid=False,tickfont=dict(size=10)),
        yaxis=dict(showgrid=True,gridcolor="#F0EBE3",title="k€/semana",tickfont=dict(size=10)),
        margin=dict(l=50,r=20,t=55,b=40),height=260,showlegend=False)
    st.plotly_chart(fig_sw,use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ANÁLISIS POR CANAL
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    tabla_data = []
    for canal in CANALES:
        h=historico_anual[canal]; o=optimo_anual[canal]
        tabla_data.append({"Canal":canal,"Inversión histórica (€)":f"{h:,.0f}",
            "Histórico (%)":f"{h/TOTAL_HIST*100:.1f}%","Contribución ventas (%)":f"{contribuciones_pct[canal]:.2f}%",
            "Inversión óptima (€)":f"{o:,.0f}","Cambio (€)":o-h,"Cambio (pp)":round(o/TOTAL_OPT*100-h/TOTAL_HIST*100,2)})
    df_t = pd.DataFrame(tabla_data)
    def _cc(v):
        if isinstance(v,(int,float)): return f"color:{C_POS};font-weight:600" if v>0 else (f"color:{C_NEG};font-weight:600" if v<0 else f"color:{C_TEXT}")
        return f"color:{C_TEXT}"
    styled = (df_t.style.map(_cc,subset=["Cambio (€)","Cambio (pp)"])
        .format({"Cambio (€)":"{:+,.0f}","Cambio (pp)":"{:+.2f}"})
        .set_properties(**{"font-family":"Inter","font-size":"13px"}).hide(axis="index"))
    st.dataframe(styled,use_container_width=True,height=320)
    st.markdown("<div style='height:.8rem;'></div>",unsafe_allow_html=True)

    # Curvas Hill
    fig_h = make_subplots(rows=2,cols=4,subplot_titles=CANALES,horizontal_spacing=.07,vertical_spacing=.22)
    ld = set()
    for idx,canal in enumerate(CANALES):
        row=idx//4+1; col=idx%4+1
        K=K_hill[canal]; alph=alphas_adstock[canal]
        x_max=2*historico_anual[canal]/52; x_w=np.linspace(0.,x_max,400)
        ads=x_w/(1.-alph); y_c=ads**ALPHA_HILL/(ads**ALPHA_HILL+K**ALPHA_HILL)
        def _pt(inv): w=inv/52.; a=w/(1.-alph); return w/1e3,a**ALPHA_HILL/(a**ALPHA_HILL+K**ALPHA_HILL)
        xh,yh=_pt(historico_anual[canal]); xo,yo=_pt(optimo_anual[canal])
        fig_h.add_trace(go.Scatter(x=x_w/1e3,y=y_c,fill="tozeroy",fillcolor="rgba(196,168,130,.1)",line=dict(color="rgba(0,0,0,0)"),showlegend=False,hoverinfo="skip"),row=row,col=col)
        fig_h.add_trace(go.Scatter(x=x_w/1e3,y=y_c,mode="lines",line=dict(color=C_ACCENT,width=2),showlegend=False),row=row,col=col)
        fig_h.add_trace(go.Scatter(x=[0,x_max/1e3],y=[.5,.5],mode="lines",line=dict(color=C_TEXT2,width=1,dash="dot"),showlegend=False,hoverinfo="skip"),row=row,col=col)
        for x_p,y_p,color,name in [(xh,yh,C_ACCENT2,"Histórico"),(xo,yo,C_POS,"Óptimo")]:
            sh=name not in ld
            if sh: ld.add(name)
            fig_h.add_trace(go.Scatter(x=[x_p],y=[y_p],mode="markers+text",marker=dict(color=color,size=10,line=dict(color="white",width=1.5)),
                text=[name],textposition="top center",textfont=dict(size=8,family="Inter",color=color),
                name=name,showlegend=sh,legendgroup=name),row=row,col=col)
    fig_h.update_layout(paper_bgcolor=C_CARD,plot_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT,size=10),
        title=dict(text="Curvas de saturación Hill por canal",font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
        legend=dict(orientation="h",yanchor="top",y=-.06,xanchor="center",x=.5,font=dict(size=11)),
        height=460,margin=dict(l=30,r=20,t=70,b=60))
    fig_h.update_xaxes(showgrid=False,tickfont=dict(size=8),title_text="k€/sem",title_font=dict(size=8),fixedrange=True)
    fig_h.update_yaxes(showgrid=True,gridcolor="#F0EBE3",range=[0,1.1],tickfont=dict(size=8),fixedrange=True)
    for ann in fig_h.layout.annotations: ann.font.size=11; ann.font.family="Inter"; ann.font.color=C_TEXT
    st.plotly_chart(fig_h,use_container_width=True)

    fig_b2=go.Figure()
    for n,d,c in [("Histórico",historico_anual,C_ACCENT2),("Óptimo",optimo_anual,C_ACCENT)]:
        fig_b2.add_trace(go.Bar(name=n,x=CANALES,y=[d[c2]/1e3 for c2 in CANALES],marker_color=c,marker_line_width=0))
    fig_b2.update_layout(barmode="group",paper_bgcolor=C_CARD,plot_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
        title=dict(text="Inversión histórica vs óptima por canal",font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
        xaxis=dict(showgrid=False,tickfont=dict(size=11)),yaxis=dict(showgrid=True,gridcolor="#F0EBE3",title="k€/año",tickfont=dict(size=11)),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=11)),
        bargap=.2,bargroupgap=.06,margin=dict(l=50,r=20,t=55,b=40),height=300)
    st.plotly_chart(fig_b2,use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SIMULADOR
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:

    # Inicializar session state con porcentajes del óptimo
    for canal in CANALES:
        if f"pct_{canal}" not in st.session_state:
            st.session_state[f"pct_{canal}"] = PCT_OPT[canal]

    st.markdown("<p style='font-family:Inter;font-size:.82rem;color:#8A8A8A;margin-bottom:.8rem;'>Ajusta el % de presupuesto por canal y el total. El simulador calcula el impacto en tiempo real.</p>",unsafe_allow_html=True)

    # Presupuesto total + botones reset
    bud_col, _, btn1_col, btn2_col = st.columns([2, .3, 1.4, 1.6])
    with bud_col:
        presupuesto_total = st.number_input(
            "Presupuesto total (€)", min_value=1_000_000, max_value=30_000_000,
            value=12_000_000, step=100_000, format="%d")
    with btn1_col:
        st.markdown("<div style='height:1.75rem'></div>",unsafe_allow_html=True)
        if st.button("↺ Restablecer óptimo", key="btn_opt"):
            for c in CANALES: st.session_state[f"pct_{c}"] = PCT_OPT[c]
    with btn2_col:
        st.markdown("<div style='height:1.75rem'></div>",unsafe_allow_html=True)
        if st.button("↺ Restablecer histórico", key="btn_hist"):
            for c in CANALES: st.session_state[f"pct_{c}"] = PCT_HIST[c]

    st.markdown("<div style='height:.3rem;'></div>",unsafe_allow_html=True)

    # Sliders en % — 2 columnas de 4
    total_prev_pct = sum(st.session_state.get(f"pct_{c}", PCT_OPT[c]) for c in CANALES)
    sl1, sl2 = st.columns(2)
    pct_sliders = {}
    simulacion_eur = {}
    for i, canal in enumerate(CANALES):
        target = sl1 if i < 4 else sl2
        with target:
            pct = st.slider(
                canal, min_value=0.0, max_value=40.0,
                step=0.5, format="%.1f %%",
                key=f"pct_{canal}",
            )
            pct_sliders[canal] = pct
            eur = pct / 100 * presupuesto_total
            simulacion_eur[canal] = eur
            st.markdown(
                f"<p style='font-family:Inter;font-size:.72rem;color:{C_TEXT2};"
                f"margin:-.5rem 0 .5rem;'>"
                f"<b style='color:{C_TEXT};'>{eur/1e3:,.0f} k€</b> · {pct:.1f}% del presupuesto</p>",
                unsafe_allow_html=True)

    total_pct   = sum(pct_sliders.values())
    total_spend = sum(simulacion_eur.values())
    pct_ok      = abs(total_pct - 100) <= 5 and 8_000_000 <= total_spend <= presupuesto_total * 1.02
    prog_color  = C_POS if pct_ok else C_NEG

    st.markdown("<div style='height:.4rem;'></div>",unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-family:Inter;font-size:.82rem;font-weight:500;color:{C_TEXT};margin-bottom:.3rem;'>"
        f"Asignación total: <b style='color:{prog_color};'>{total_pct:.1f}%</b> "
        f"({total_spend/1e6:.2f} M€)"
        f"{'  ✓' if pct_ok else '  ⚠ ajusta los % para sumar ~100%'}</p>",
        unsafe_allow_html=True)
    prog = min(total_pct / 100, 1.2)
    st.markdown(
        f"<div style='background:#E8E0D6;border-radius:6px;height:8px;'>"
        f"<div style='background:{prog_color};width:{min(prog,1)*100:.1f}%;"
        f"height:8px;border-radius:6px;'></div></div>",
        unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>",unsafe_allow_html=True)

    # KPIs de simulación
    ventas_mkt_sim = calcular_ventas_marketing(simulacion_eur)
    v_incr         = ventas_mkt_sim - ventas_mkt_hist
    roi_sim        = v_incr / total_spend * 100 if total_spend > 0 else 0
    mejora_pct     = v_incr / ventas_mkt_hist * 100 if ventas_mkt_hist > 0 else 0
    canal_max      = max(pct_sliders, key=pct_sliders.get)

    kk1,kk2,kk3,kk4 = st.columns(4)
    with kk1: st.markdown(kpi_card("Presupuesto asignado",f"{total_spend/1e6:.2f} M€",color=prog_color,sub=f"{total_pct:.1f}% del total ({presupuesto_total/1e6:.0f} M€)"),unsafe_allow_html=True)
    with kk2: st.markdown(kpi_card("ROI incremental est.",f"{roi_sim:+.2f}%",color=C_POS if roi_sim>=0 else C_NEG,sub="ventas inc. / presupuesto total"),unsafe_allow_html=True)
    with kk3: st.markdown(kpi_card("Mejora ventas marketing",f"{mejora_pct:+.1f}%",color=C_POS if mejora_pct>=0 else C_NEG,sub="vs distribución histórica"),unsafe_allow_html=True)
    with kk4: st.markdown(kpi_card("Canal dominante",canal_max,color=C_ACCENT,sub=f"{pct_sliders[canal_max]:.1f}% del presupuesto"),unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>",unsafe_allow_html=True)

    # ── ROAS y coste por euro por canal ───────────────────────────────────────
    st.markdown("<h3 style='font-family:Playfair Display,serif;font-size:1.05rem;color:#2C2C2C;margin-bottom:.6rem;font-weight:600;'>ROAS y eficiencia por canal</h3>",unsafe_allow_html=True)

    # Estimación de contribución por canal en EUR (escalando por Hill ratio vs histórico)
    roas_data = []
    for canal in CANALES:
        hill_hist = _hill(historico_anual[canal], canal)
        hill_sim  = _hill(simulacion_eur[canal],  canal)
        ratio     = hill_sim / hill_hist if hill_hist > 0 else 0
        contrib_hist_eur = contribuciones_pct[canal] / 100 * media_anual
        contrib_sim_eur  = contrib_hist_eur * ratio
        inv_sim          = simulacion_eur[canal]
        roas             = contrib_sim_eur / inv_sim if inv_sim > 0 else 0
        coste_euro       = inv_sim / contrib_sim_eur if contrib_sim_eur > 0 else 0
        roas_data.append({
            "Canal": canal,
            "Inversión (k€)": round(inv_sim/1e3, 0),
            "% del total": round(pct_sliders[canal], 1),
            "Contrib. est. (k€)": round(contrib_sim_eur/1e3, 0),
            "ROAS": round(roas, 2),
            "Coste por € generado": round(coste_euro, 2),
        })
    df_roas = pd.DataFrame(roas_data)

    def _roas_color(v):
        if isinstance(v, (int, float)):
            if v >= 5:   return f"color:{C_POS};font-weight:600"
            elif v >= 2: return f"color:{C_ACCENT};font-weight:600"
            elif v > 0:  return f"color:{C_NEG}"
        return f"color:{C_TEXT}"

    styled_r = (df_roas.style
        .map(_roas_color, subset=["ROAS"])
        .format({"Inversión (k€)":"{:,.0f}","Contrib. est. (k€)":"{:,.0f}","% del total":"{:.1f}%","ROAS":"{:.2f}x","Coste por € generado":"€{:.2f}"})
        .set_properties(**{"font-family":"Inter","font-size":"13px"})
        .hide(axis="index"))
    st.dataframe(styled_r, use_container_width=True, height=290)

    st.markdown("<div style='height:.8rem;'></div>",unsafe_allow_html=True)

    # Gráficos: barras distribución + gauge
    viz1, viz2 = st.columns([55, 45])

    with viz1:
        pct_h = {c: historico_anual[c]/TOTAL_HIST*100 for c in CANALES}
        pct_s = pct_sliders
        orden = sorted(CANALES, key=lambda c: pct_s[c])
        fig_hb = go.Figure()
        for nv,dv,cv in [("Histórico",pct_h,C_ACCENT2),("Simulación",pct_s,C_ACCENT)]:
            fig_hb.add_trace(go.Bar(name=nv,orientation="h",x=[dv[c] for c in orden],y=orden,marker_color=cv,marker_line_width=0))
        fig_hb.update_layout(barmode="group",paper_bgcolor=C_CARD,plot_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
            title=dict(text="Distribución del presupuesto (%)",font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
            xaxis=dict(showgrid=False,title="% del presupuesto",tickfont=dict(size=10)),
            yaxis=dict(showgrid=False,tickfont=dict(size=10)),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=11)),
            bargap=.25,bargroupgap=.05,margin=dict(l=20,r=20,t=55,b=30),height=320)
        st.plotly_chart(fig_hb,use_container_width=True)

    with viz2:
        roi_max = roi_optimo * 1.6
        roi_min = min(roi_sim - abs(roi_optimo)*.4, -3)
        fig_g = go.Figure(go.Indicator(mode="gauge+number+delta",value=roi_sim,
            number=dict(suffix="%",font=dict(family="Playfair Display",size=26,color=C_TEXT)),
            delta=dict(reference=roi_optimo,relative=False,suffix="pp vs óptimo",font=dict(size=11)),
            gauge=dict(axis=dict(range=[roi_min,roi_max],tickfont=dict(size=9,family="Inter")),
                bar=dict(color=C_ACCENT,thickness=.28),bgcolor=C_CARD,borderwidth=0,
                steps=[dict(range=[roi_min,0],color="#FADDD4"),
                       dict(range=[0,roi_optimo*.55],color="#FDF5EE"),
                       dict(range=[roi_optimo*.55,roi_max],color="#E4EDE5")],
                threshold=dict(line=dict(color=C_POS,width=3),thickness=.75,value=roi_optimo))))
        fig_g.add_annotation(text=f"Óptimo: {roi_optimo:.2f}%",x=.5,y=.15,showarrow=False,
            font=dict(family="Inter",size=10,color=C_POS))
        fig_g.update_layout(paper_bgcolor=C_CARD,font=dict(family="Inter",color=C_TEXT),
            title=dict(text="ROI incremental vs óptimo posible",font=dict(family="Playfair Display",size=13,color=C_TEXT),x=0),
            margin=dict(l=20,r=20,t=55,b=10),height=320)
        st.plotly_chart(fig_g,use_container_width=True)

    # ── Descarga CSV ──────────────────────────────────────────────────────────
    st.markdown("<div style='height:.6rem;'></div>",unsafe_allow_html=True)
    df_dl = pd.DataFrame([{
        "Canal": c,
        "Inversion_historica_EUR": historico_anual[c],
        "Pct_historico": PCT_HIST[c],
        "Inversion_optima_EUR": optimo_anual[c],
        "Pct_optimo": PCT_OPT[c],
        "Pct_simulacion": round(pct_sliders[c],1),
        "Inversion_simulacion_EUR": round(simulacion_eur[c]),
        "ROAS_simulacion": next(r["ROAS"] for r in roas_data if r["Canal"]==c),
    } for c in CANALES])
    df_dl.loc[len(df_dl)] = {
        "Canal":"TOTAL","Inversion_historica_EUR":TOTAL_HIST,
        "Pct_historico":100,"Inversion_optima_EUR":TOTAL_OPT,"Pct_optimo":100,
        "Pct_simulacion":round(total_pct,1),"Inversion_simulacion_EUR":round(total_spend),"ROAS_simulacion":"",
    }
    csv_str = df_dl.to_csv(index=False)
    dc1,_,dc2 = st.columns([2,4,2])
    with dc1:
        st.download_button(
            label="📥 Descargar resultados CSV",
            data=csv_str,
            file_name="kmoda_mmm_simulacion.csv",
            mime="text/csv")
    with dc2:
        st.markdown(
            f"<p style='font-family:Inter;font-size:.75rem;color:{C_TEXT2};text-align:right;padding-top:.6rem;'>"
            f"R²={R2_DISPLAY} · MAPE={MAPE_DISPLAY:.2f}% · Modelo Ridge v3</p>",
            unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — METODOLOGÍA
# ═══════════════════════════════════════════════════════════════════════════════


def html_table(headers, rows):
    th = "padding:.35rem .7rem;color:#2C2C2C;background:#F0EBE3;font-family:Inter,sans-serif;font-size:.82rem;font-weight:600;text-align:left;border-bottom:2px solid #E8E0D6;"
    td = "padding:.3rem .7rem;font-family:Inter,sans-serif;font-size:.82rem;border-bottom:1px solid #F0EBE3;color:#2C2C2C;"
    h  = '<table style="width:100%;border-collapse:collapse;background:#FFFFFF;border-radius:6px;overflow:hidden;">'
    h += '<thead><tr>' + ''.join(f'<th style="{th}">{x}</th>' for x in headers) + '</tr></thead><tbody>'
    for i, row in enumerate(rows):
        bg = "#FFFFFF" if i%2==0 else "#FAFAFA"
        h += f'<tr style="background:{bg};">' + ''.join(f'<td style="{td}">{cell}</td>' for cell in row) + '</tr>'
    return h + '</tbody></table>'

with tab5:
    st.markdown(
        "<h2 style='font-family:Playfair Display,serif;font-size:1.4rem;font-weight:700;"
        "color:#2C2C2C;margin-bottom:1rem;'>Metodología del modelo MMM</h2>",
        unsafe_allow_html=True)

    col_m1, col_m2 = st.columns([55, 45])

    with col_m1:
        # 1 — Adstock
        tipo_efecto = lambda a: (
            "Respuesta rápida"    if a <= 0.1 else
            "Efecto corto plazo"  if a <= 0.2 else
            "Efecto medio plazo"  if a <= 0.3 else
            "Construcción de marca")
        rows_ads = [[c, str(alphas_adstock[c]), tipo_efecto(alphas_adstock[c])] for c in CANALES]
        tbl_ads  = html_table(["Canal", "α adstock", "Tipo de efecto"], rows_ads)

        st.markdown(
            f"<div style='background:#FFFFFF;border-radius:10px;padding:1.2rem 1.5rem;"
            f"border:1px solid {C_BORDER};margin-bottom:.8rem;'>"
            f"<h4 style='font-family:Playfair Display,serif;font-size:1rem;color:{C_ACCENT};"
            "margin-bottom:.5rem;'>1 · Transformación Adstock</h4>"
            f"<p style='font-family:Inter;font-size:.85rem;color:{C_TEXT};line-height:1.7;'>"
            "Modela el <b>efecto acumulado y de decaimiento</b> de la publicidad:</p>"
            "<p style='font-family:Inter;font-size:.92rem;background:#F5F0EA;padding:.6rem 1rem;"
            "border-radius:6px;text-align:center;color:#2C2C2C;'><b>A(t) = inv(t) + α · A(t−1)</b></p>"
            f"<p style='font-family:Inter;font-size:.83rem;color:{C_TEXT2};margin:.5rem 0;'>"
            "Tras el adstock se aplica un <b>lag de 1 semana</b>.</p>"
            + tbl_ads + "</div>",
            unsafe_allow_html=True)

        # 2 — Hill
        rows_hill = [[c, f"{K_hill[c]:,}"] for c in CANALES]
        tbl_hill  = html_table(["Canal", "K (€/sem)"], rows_hill)

        st.markdown(
            f"<div style='background:#FFFFFF;border-radius:10px;padding:1.2rem 1.5rem;"
            f"border:1px solid {C_BORDER};margin-bottom:.8rem;'>"
            f"<h4 style='font-family:Playfair Display,serif;font-size:1rem;color:{C_ACCENT};"
            "margin-bottom:.5rem;'>2 · Función de saturación Hill</h4>"
            f"<p style='font-family:Inter;font-size:.85rem;color:{C_TEXT};line-height:1.7;'>"
            "Captura los <b>rendimientos decrecientes</b>. Mapea inversión → [0, 1]:</p>"
            "<p style='font-family:Inter;font-size:.92rem;background:#F5F0EA;padding:.6rem 1rem;"
            "border-radius:6px;text-align:center;color:#2C2C2C;'><b>Hill(x) = x² / (x² + K²)</b></p>"
            f"<p style='font-family:Inter;font-size:.83rem;color:{C_TEXT2};margin:.5rem 0;'>"
            "<b>K</b> = mediana histórica de inversión semanal (semi-saturación).</p>"
            + tbl_hill + "</div>",
            unsafe_allow_html=True)

    with col_m2:
        # 3 — Ridge
        def _efecto_color(v):
            if v < 1:   return f"<span style='color:#7A9E7E;font-weight:600;'>Potenciado</span>"
            elif v > 1: return f"<span style='color:#C47A5A;font-weight:600;'>Reducido</span>"
            return "<span style='color:#8A8A8A;'>Neutro</span>"

        rows_pen = [[c, str(penalizacion[c]), _efecto_color(penalizacion[c])] for c in CANALES]
        tbl_pen  = html_table(["Canal", "Factor pen.", "Efecto"], rows_pen)

        st.markdown(
            f"<div style='background:#FFFFFF;border-radius:10px;padding:1.2rem 1.5rem;"
            f"border:1px solid {C_BORDER};margin-bottom:.8rem;'>"
            f"<h4 style='font-family:Playfair Display,serif;font-size:1rem;color:{C_ACCENT};"
            "margin-bottom:.5rem;'>3 · Ridge con penalización diferenciada</h4>"
            f"<p style='font-family:Inter;font-size:.85rem;color:{C_TEXT};line-height:1.7;'>"
            "<b>Ridge regression</b> (L2) controla multicolinealidad. V3 aplica penalización por canal:</p>"
            "<p style='font-family:Inter;font-size:.92rem;background:#F5F0EA;padding:.6rem 1rem;"
            "border-radius:6px;text-align:center;color:#2C2C2C;'><b>min ||y − Xβ||² + λ · Σᵢ (penᵢ · βᵢ)²</b></p>"
            f"<p style='font-family:Inter;font-size:.8rem;color:{C_TEXT2};margin:.5rem 0;'>"
            "α Ridge óptimo via <b>validación cruzada CV=5</b> en [1, 100.000].</p>"
            + tbl_pen + "</div>",
            unsafe_allow_html=True)

        # 4 — B0
        st.markdown(
            f"<div style='background:#FFFFFF;border-radius:10px;padding:1.2rem 1.5rem;"
            f"border:1px solid {C_BORDER};'>"
            f"<h4 style='font-family:Playfair Display,serif;font-size:1rem;color:{C_ACCENT};"
            "margin-bottom:.5rem;'>4 · Descomposición de ventas (B0)</h4>"
            "<p style='font-family:Inter;font-size:.88rem;background:#F5F0EA;padding:.6rem 1rem;"
            "border-radius:6px;color:#2C2C2C;'><b>Ventas = B0 + Σ contrib_canal + Estacionalidad</b></p>"
            f"<p style='font-family:Inter;font-size:.83rem;color:{C_TEXT2};margin-top:.5rem;line-height:1.7;'>"
            "• <b>B0</b> = ventas sin inversión publicitaria<br>"
            "• contrib_canal = β × Σ adstock / σ<br>"
            "• B0 = n × (intercept − Σ βᵢ · μᵢ / σᵢ)</p>"
            f"<div style='background:#EEF4EF;border-left:3px solid {C_POS};padding:.6rem .8rem;"
            "border-radius:4px;margin-top:.6rem;'>"
            f"<p style='font-family:Inter;font-size:.82rem;color:#2C2C2C;margin:0;'>"
            f"<b>Resultados modelo v3:</b><br>"
            f"R² = {R2_DISPLAY} &nbsp;·&nbsp; MAPE = {MAPE_DISPLAY:.2f}% &nbsp;·&nbsp; B0 = {B0_pct:.1f}%<br>"
            "α Ridge = 756 &nbsp;·&nbsp; 260 semanas (2020-2024)</p></div></div>",
            unsafe_allow_html=True)

    # Gráfico contribuciones
    comp   = list(contribuciones_pct.keys()) + ["B0 Baseline"]
    vals   = list(contribuciones_pct.values()) + [B0_pct]
    colrs  = [C_ACCENT]*len(contribuciones_pct) + [C_ACCENT2]
    orden2 = np.argsort(vals)
    fig_mc = go.Figure(go.Bar(
        x=[vals[i] for i in orden2], y=[comp[i] for i in orden2],
        orientation="h", marker_color=[colrs[i] for i in orden2], marker_line_width=0,
        text=[f"{vals[i]:.1f}%" for i in orden2], textposition="outside",
        textfont=dict(family="Inter", size=10, color=C_TEXT)))
    fig_mc.update_layout(
        paper_bgcolor=C_CARD, plot_bgcolor=C_CARD,
        font=dict(family="Inter", color=C_TEXT),
        title=dict(text="Contribución de cada componente a las ventas totales",
                   font=dict(family="Playfair Display", size=13, color=C_TEXT), x=0),
        xaxis=dict(showgrid=False, showticklabels=False, range=[0, 75]),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
        margin=dict(l=20, r=60, t=55, b=20), height=320)
    st.plotly_chart(fig_mc, use_container_width=True)

# streamlit run app.py
