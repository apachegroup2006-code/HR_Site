import streamlit as st
import pandas as pd
import os
import subprocess
import sys
from datetime import datetime, date
import io
import base64

# Автоматическая установка xlsxwriter
try:
    import xlsxwriter
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])

# --- НАСТРОЙКИ ПОЛЬЗОВАТЕЛЕЙ И ФАЙЛОВ ---
USERS = {
    "admin": {"password": "123", "role": "admin"},
    "user": {"password": "111", "role": "employee"},
    "user2": {"password": "222", "role": "history_only"} # Твой новый пользователь
}

DB_FILE = 'hr_data.csv'
DEPT_FILE = 'departments.csv'
PROD_DB_FILE = 'production_violations.csv'  # База производства
PROD_DEPT_FILE = 'production_depts.csv'     # Отделы производства
LOGO_PATH = 'logo.png'

# --- ЗАГРУЗКА ДАННЫХ (HR) ---
if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE).fillna("")
else:
    df = pd.DataFrame(columns=['ԱԱՀ', 'Բաժին', 'Կարգավիճակ', 'Պատմություն'])

if os.path.exists(DEPT_FILE):
    depts = pd.read_csv(DEPT_FILE)['название'].tolist()
else:
    depts = ["IT", "HR", "Մարքեթինգ"]
    pd.DataFrame({'название': depts}).to_csv(DEPT_FILE, index=False)

# --- ЗАГРУЗКА ДАННЫХ (ПРОИЗВОДСТВО) ---
if os.path.exists(PROD_DB_FILE):
    df_prod = pd.read_csv(PROD_DB_FILE).fillna("")
else:
    df_prod = pd.DataFrame(columns=['Աշխատակից', 'Ստորաբաժանում', 'Պատմություն'])

if os.path.exists(PROD_DEPT_FILE):
    prod_depts = pd.read_csv(PROD_DEPT_FILE)['название'].tolist()
else:
    prod_depts = ["Արտադրամաս 1", "Արտադրամաս 2"]
    pd.DataFrame({'название': prod_depts}).to_csv(PROD_DEPT_FILE, index=False)

st.set_page_config(page_title="ԱՊԱՉԵ", layout="wide")

# --- ФУНКЦИИ ---
def get_base64_logo():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def count_records_in_range(history_str, start, end):
    if not history_str: return 0
    count = 0
    hists = [r for r in str(history_str).split('; ') if r]
    for rec in hists:
        try:
            r_date_str = rec.split(' | ')[0]
            r_date = datetime.strptime(r_date_str, '%d.%m.%Y').date()
            if start <= r_date <= end: count += 1
        except: continue
    return count

# --- CSS: ТВОЙ СТАНДАРТ ---
st.markdown("""
    <style>
    @keyframes smoothFade {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stHorizontalBlock {
        animation: smoothFade 0.6s ease-out forwards;
    }
    .neon-logo { 
        display: block; 
        margin-left: auto; 
        margin-right: auto; 
        filter: drop-shadow(0 0 5px #fff) drop-shadow(0 0 10px #00d2ff); 
        transition: 0.5s ease; 
    }
    .neon-logo:hover { 
        filter: drop-shadow(0 0 10px #fff) drop-shadow(0 0 30px #00d2ff); 
        cursor: pointer;
    }
    button { 
        border-radius: 10px !important;
        transition: all 0.3s !important; 
    }
    button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'user_role' not in st.session_state: st.session_state['user_role'] = None
if 'page' not in st.session_state: st.session_state['page'] = 'login'

# --- 1. СТРАНИЦА ВХОДА ---
if not st.session_state['auth']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        logo_b64 = get_base64_logo()
        if logo_b64: st.markdown(f'<img src="data:image/png;base64,{logo_b64}" class="neon-logo" style="width:100%;">', unsafe_allow_html=True)
        with st.form("login_form"):
            l_in = st.text_input("Լոգին")
            p_in = st.text_input("Գաղտնաբառ", type="password")
            if st.form_submit_button("Մուտք", use_container_width=True):
                if l_in in USERS and USERS[l_in]["password"] == p_in:
                    st.session_state['auth'] = True
                    st.session_state['user_role'] = USERS[l_in]["role"]
                    st.session_state['page'] = 'menu'
                    st.rerun()
                else: st.error("Մուտքի սխալ")

# --- 2. ГЛАВНОЕ МЕНЮ ---
elif st.session_state['page'] == 'menu':
    st.sidebar.button("🚪 Ելք", on_click=lambda: st.session_state.update({'auth': False}))
    _, col_logo_center, _ = st.columns([1, 0.8, 1])
    with col_logo_center:
        logo_b64 = get_base64_logo()
        if logo_b64: st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:100%;">', unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center;'>Ընտրեք համակարգի բաժինը</h1>", unsafe_allow_html=True)
    st.write("---")
    _, col_menu, _ = st.columns([1, 1, 1])
    with col_menu:
        # ЛОГИКА ДЛЯ user2 (Начальник цеха - только история)
        if st.session_state['user_role'] == 'history_only':
            if st.button("📜 ԱՐՏԱԴՐՈՒԹՅԱՆ ՊԱՏՄՈՒԹՅՈՒՆ", use_container_width=True, type="primary"):
                st.session_state['page'] = 'prod_all_history'
                st.rerun()
        
        # ЛОГИКА ДЛЯ admin
        elif st.session_state['user_role'] == 'admin':
            if st.button("👥 HR Գործառույթներ", use_container_width=True, type="primary"):
                st.session_state['page'] = 'hr_panel'
                st.rerun()
            if st.button("🏭 Արտադրություն", use_container_width=True):
                st.session_state['page'] = 'prod_panel'
                st.rerun()
            if st.button("📜 ԱՐՏԱԴՐՈՒԹՅԱՆ ՊԱՏՄՈՒԹՅՈՒՆ", use_container_width=True):
                st.session_state['page'] = 'prod_all_history'
                st.rerun()
            st.button("📦 Պահեստ", use_container_width=True)
            st.button("💰 Ֆինանսներ", use_container_width=True)
        
        # ЛОГИКА ДЛЯ employee
        else:
            if st.button("👥 HR Գործառույթներ", use_container_width=True, type="primary"):
                st.session_state['page'] = 'hr_panel'
                st.rerun()

# --- 3. СТРАНИЦА ПОЛНОЙ ИСТОРИИ (HR) ---
elif st.session_state['page'] == 'history_page':
    i = st.session_state.get('edit_idx')
    if i is not None and i < len(df):
        if st.button("⬅️ Հետ դեպի HR պանել"):
            st.session_state['page'] = 'hr_panel'
            st.rerun()
        st.title(f"📜 Ամբողջ պատմությունը: {df.at[i, 'ԱԱՀ']}")
        hists = [r for r in str(df.at[i, 'Պատմություն']).split('; ') if r]
        for h_idx, record in enumerate(reversed(hists)):
            real_idx = len(hists) - 1 - h_idx
            c_txt, c_del = st.columns([10, 1])
            with c_txt:
                if "Անձնական" in record: st.error(record)
                else: st.info(record)
            with c_del:
                if st.button("❌", key=f"f_del_{real_idx}"):
                    hists.pop(real_idx)
                    df.at[i, 'Պատմություն'] = "; ".join(hists) + ("; " if hists else "")
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()

# --- 4. HR ПАНЕЛЬ (НЕИЗМЕННАЯ) ---
elif st.session_state['page'] == 'hr_panel':
    is_admin = st.session_state['user_role'] == 'admin'
    if st.sidebar.button("🏠 ԳԼԽԱՎՈՐ ՄԵՆՅՈՒ", use_container_width=True):
        st.session_state['page'] = 'menu'
        st.rerun()
    
    logo_b64 = get_base64_logo()
    if logo_b64: st.sidebar.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:100%; margin-bottom: 10px;">', unsafe_allow_html=True)

    st.sidebar.header("⚙️ Կարգավորումներ")
    d_from = st.sidebar.date_input("Սկիզբ", date.today())
    d_to = st.sidebar.date_input("Ավարտ", date.today())

    if is_admin:
        if st.sidebar.button("📥 Պատրաստել Excel"):
            export_list = []
            for _, row in df.iterrows():
                hists = [r for r in str(row['Պատմություն']).split('; ') if r]
                for rec in hists:
                    try:
                        r_date = datetime.strptime(rec.split(' | ')[0], '%d.%m.%Y').date()
                        if d_from <= r_date <= d_to:
                            export_list.append({'Ամսաթիվ': rec.split(' | ')[0], 'Աշխատակից': row['ԱԱՀ'], 'Բաժին': row['Բաժին'], 'Գրառում': rec.split(' | ')[1]})
                    except: continue
            if export_list:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer: pd.DataFrame(export_list).to_excel(writer, index=False)
                st.sidebar.download_button("📎 Ներբեռնել", output.getvalue(), f"Report_{date.today()}.xlsx")

        with st.sidebar.expander("📂 Բաժիններ"):
            n_d = st.text_input("Նոր բաժին")
            if st.button("➕ Ավելացնել"):
                if n_d and n_d not in depts:
                    depts.append(n_d)
                    pd.DataFrame({'название': depts}).to_csv(DEPT_FILE, index=False)
                    st.rerun()

        st.sidebar.subheader("👔 Նոր աշխատակից")
        with st.sidebar.form("add_worker", clear_on_submit=True):
            n_n = st.text_input("ԱԱՀ")
            n_dep = st.selectbox("Բաժին", depts)
            if st.form_submit_button("Ստեղծել"):
                if n_n:
                    new_row = {'ԱԱՀ': n_n, 'Բաժին': n_dep, 'Կարգավիճակ': '', 'Պատմություն': ''}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()

    st.title("📂 HR Գործառույթներ")
    sel_o = st.selectbox("Ֆիլտր ըստ բաժնի:", ["Բոլորը"] + depts)
    search_q = st.text_input("🔍 Որոնում", "").lower()
    
    disp_df = df.copy()
    if sel_o != "Բոլորը": disp_df = disp_df[disp_df['Բաժին'] == sel_o]
    if search_q: disp_df = disp_df[disp_df['ԱԱՀ'].str.lower().str.contains(search_q)]

    for idx, row in disp_df.iterrows():
        c_b, c_i, c_d = st.columns([4, 2, 1])
        rec_count = count_records_in_range(row['Պատմություն'], d_from, d_to)
        with c_b:
            if st.button(f"[{rec_count}] {row['ԱԱՀ']}", key=f"u_{idx}", use_container_width=True):
                st.session_state['edit_idx'] = idx
        with c_i: st.write(f"🏢 {row['Բաժին']}")
        with c_d:
            if is_admin:
                if st.button("🗑️", key=f"del_w_{idx}"):
                    df = df.drop(idx).reset_index(drop=True)
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()

    if 'edit_idx' in st.session_state:
        i = st.session_state['edit_idx']
        if i < len(df):
            st.divider()
            st.header(f"👔 {df.at[i, 'ԱԱՀ']}")
            l, r = st.columns(2)
            with l:
                if is_admin:
                    new_loc = st.selectbox("Տեղափոխել բաժին", depts, index=depts.index(df.at[i, 'Բաժին']) if df.at[i, 'Բաժին'] in depts else 0)
                    if st.button("🚀 Տեղափոխել"):
                        df.at[i, 'Բաժին'] = new_loc
                        df.to_csv(DB_FILE, index=False)
                        st.rerun()
                
                dt = st.date_input("Ամսաթիվ", date.today())
                stt = st.selectbox("Կարգավիճակ", ["Գործնական բացակայություն", "Անձնական բացակայություն"])
                cm = st.text_area("Մեկնաբանություն")
                if st.button("✅ Պահպանել"):
                    h = str(df.at[i, 'Պատմություն']) if pd.notna(df.at[i, 'Պատմություն']) else ""
                    df.at[i, 'Պատմություն'] = h + f"{dt.strftime('%d.%m.%Y')} | {stt}: {cm}; "
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
            with r:
                st.subheader("🕒 Վերջին 3 գրառումները")
                hists = [rec for rec in str(df.at[i, 'Պատմություն']).split('; ') if rec]
                for ridx, rec in enumerate(list(reversed(hists))[:3]):
                    c_t, c_x = st.columns([10, 1])
                    with c_t:
                        if "Անձնական" in rec: st.error(rec)
                        else: st.info(rec)
                    with c_x:
                        if st.button("❌", key=f"dl_{ridx}"):
                            hists.pop(-(ridx+1))
                            df.at[i, 'Պատմություն'] = "; ".join(hists) + ("; " if hists else "")
                            df.to_csv(DB_FILE, index=False)
                            st.rerun()
                if len(hists) > 0:
                    if st.button("📜 Տեսնել ամբողջ պատմությունը", use_container_width=True):
                        st.session_state['page'] = 'history_page'
                        st.rerun()
# --- 5. ՊԱՆԵԼ ՊՐՈԴՈՒԿՑԻԱՅԻ (ԹԱՐՄԱՑՎԱԾ ՏԵՍԱԿՆԵՐՈՎ) ---
elif st.session_state['page'] == 'prod_panel':
    if st.sidebar.button("🏠 ԳԼԽԱՎՈՐ ՄԵՆՅՈՒ", use_container_width=True):
        st.session_state['page'] = 'menu'
        st.rerun()

    logo_b64 = get_base64_logo()
    if logo_b64: st.sidebar.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:100%; margin-bottom: 10px;">', unsafe_allow_html=True)

    st.title("🏭 Արտադրության Կառավարում")

    # --- ՍԱՅԴԲԱՐ: ԲԱԺԻՆՆԵՐԻ ԿԱՌԱՎԱՐՈՒՄ ---
    with st.sidebar.expander("📂 Բաժինների Կառավարում"):
        new_p_d = st.text_input("Նոր արտադրամաս")
        if st.button("➕ Ավելացնել", key="add_p_dept"):
            if new_p_d and new_p_d not in prod_depts:
                prod_depts.append(new_p_d)
                pd.DataFrame({'название': prod_depts}).to_csv(PROD_DEPT_FILE, index=False)
                st.rerun()
        
        st.divider()
        if st.session_state.get('user_role') == 'admin':
            st.write("🗑️ Հեռացնել բաժինը")
            for d_idx, d_name in enumerate(prod_depts):
                d_col1, d_col2 = st.columns([4, 1])
                d_col1.write(d_name)
                if d_col2.button("🗑️", key=f"del_dept_{d_idx}"):
                    prod_depts.pop(d_idx)
                    pd.DataFrame({'название': prod_depts}).to_csv(PROD_DEPT_FILE, index=False)
                    st.rerun()

    st.sidebar.subheader("👔 Նոր Աշխատակից")
    with st.sidebar.form("add_prod_worker", clear_on_submit=True):
        p_n = st.text_input("ԱԱՀ")
        p_dep = st.selectbox("Արտադրամաս", prod_depts)
        if st.form_submit_button("Ստեղծել"):
            if p_n:
                new_p_row = {'Աշխատակից': p_n, 'Ստորաբաժանում': p_dep, 'Պատմություն': ''}
                df_prod = pd.concat([df_prod, pd.DataFrame([new_p_row])], ignore_index=True)
                df_prod.to_csv(PROD_DB_FILE, index=False)
                st.rerun()

    p_search = st.text_input("🔍 Որոնել աշխատակցին (անունով)", "").lower()
    p_filter_dept = st.selectbox("Ֆիլտր ըստ արտադրամասի:", ["Բոլորը"] + prod_depts)
    
    p_disp = df_prod.copy()
    if p_filter_dept != "Բոլորը":
        p_disp = p_disp[p_disp['Ստորաբաժանում'] == p_filter_dept]
    if p_search:
        p_disp = p_disp[p_disp['Աշխատակից'].str.lower().str.contains(p_search)]

    for p_idx, p_row in p_disp.iterrows():
        col1, col2, col3 = st.columns([4, 2, 1])
        with col1:
            if st.button(f"👔 {p_row['Աշխատակից']}", key=f"p_u_{p_idx}", use_container_width=True):
                st.session_state['p_edit_idx'] = p_idx
        with col2: st.write(f"🏭 {p_row['Ստորաբաժանում']}")
        with col3:
            if st.button("🗑️", key=f"p_del_{p_idx}"):
                df_prod = df_prod.drop(p_idx).reset_index(drop=True)
                df_prod.to_csv(PROD_DB_FILE, index=False)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📜 Տեսնել ամբողջական պատմությունը", use_container_width=True, type="primary"):
        st.session_state['page'] = 'prod_all_history'
        st.rerun()

    if 'p_edit_idx' in st.session_state:
        pi = st.session_state['p_edit_idx']
        if pi < len(df_prod):
            st.divider()
            st.header(f"👔 {df_prod.at[pi, 'Աշխատակից']}")
            pl, pr = st.columns(2)
            with pl:
                st.subheader("⚠️ Գրանցել նոր խախտում")
                p_date_incident = st.date_input("Խախտման ամսաթիվ", date.today())
                # ОБНОВЛЕННЫЕ ТИПЫ НАРУШЕНИЙ
                p_type = st.selectbox("Տեսակ", ["Սանիտարական", "Կարգապահական", "Տեխնոլոգիական", "Անվտանգություն", "Այլ"])
                p_link = st.text_input("📁 Ֆայլի ուղին", help="Օրինակ՝ C:\\Videos\\record.mp4")
                p_comm = st.text_area("Նկարագրություն")
                
                if st.button("💾 Պահպանել", use_container_width=True):
                    p_hist = str(df_prod.at[pi, 'Պատմություն']) if pd.notna(df_prod.at[pi, 'Պատմություն']) else ""
                    # Сохраняем дату и время создания для точной сортировки
                    reg_now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                    entry = f"{p_date_incident.strftime('%d.%m.%Y')} | {p_type} | {p_link.replace('\"','')} | {p_comm} | Սպասվում է | - | {reg_now}; "
                    df_prod.at[pi, 'Պատմություն'] = p_hist + entry
                    df_prod.to_csv(PROD_DB_FILE, index=False)
                    st.success("Գրանցված է")
                    st.rerun()

            with pr:
                st.subheader("🕒 Վերջին 3 գրառումները")
                p_hists = [r for r in str(df_prod.at[pi, 'Պատմություն']).split('; ') if r]
                for ph in reversed(p_hists[-3:]): st.error(ph)

# --- 6. ԱՄԲՈՂՋԱԿԱՆ ՊԱՏՄՈՒԹՅՈՒՆ (ՍՈՐՏԱՎՈՐՈՒՄ, ԷՔՍՊՈՐՏ ԵՎ ՍԻՆԽՐՈՆԱՑՈՒՄ) ---
elif st.session_state['page'] == 'prod_all_history':
    
    # Կոճակների տեսքը ըստ դերի
    if st.session_state['user_role'] == 'history_only':
        if st.button("⬅️ Հետ դեպի Մենյու", use_container_width=True):
            st.session_state['page'] = 'menu'
            st.rerun()
    else:
        if st.button("⬅️ Հետ դեպի Արտադրություն", use_container_width=True):
            st.session_state['page'] = 'prod_panel'
            st.rerun()
    
    st.title("📜 Արտադրության ամբողջական պատմություն")
    
    # --- ԻՆՏԵՐՎԱԼԱՅԻՆ ՕՐԱՑՈՒՅՑ ---
    st.subheader("📅 Ընտրեք ստեղծման ժամանակահատվածը")
    today = date.today()
    start_of_month = today.replace(day=1)
    date_range = st.date_input("Ժամանակահատված", value=(start_of_month, today))

    # --- ՖԻԼՏՐՆԵՐ ---
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        sel_dept = st.selectbox("Բաժին", ["Բոլորը"] + prod_depts)
    
    if sel_dept == "Բոլորը":
        available_workers = df_prod['Աշխատակից'].unique().tolist()
    else:
        available_workers = df_prod[df_prod['Ստորաբաժանում'] == sel_dept]['Աշխատակից'].unique().tolist()
        
    with f_col2:
        sel_worker = st.selectbox("Աշխատակից", ["Բոլորը"] + available_workers)
    
    with f_col3:
        search_all = st.text_input("🔍 Որոնել", "")

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        d_start, d_end = date_range
        # Միշտ կարդում ենք թարմ տվյալները ֆայլից
        temp_df = pd.read_csv(PROD_DB_FILE).fillna("")
        all_logs = []
        
        for p_idx, row in temp_df.iterrows():
            if sel_dept != "Բոլորը" and row['Ստորաբաժանում'] != sel_dept: continue
            if sel_worker != "Բոլորը" and row['Աշխատակից'] != sel_worker: continue
            
            entries = [e for e in str(row['Պատմություն']).split('; ') if e]
            for e_idx, e in enumerate(entries):
                parts = [p.strip() for p in e.split(' | ')]
                if len(parts) < 5: continue
                
                reg_dt_str = parts[6] if len(parts) > 6 else parts[0]
                try:
                    if ' ' in reg_dt_str:
                        reg_dt_obj = datetime.strptime(reg_dt_str, '%d.%m.%Y %H:%M:%S')
                    else:
                        reg_dt_obj = datetime.strptime(reg_dt_str, '%d.%m.%Y')
                    reg_date_only = reg_dt_obj.date()
                except: continue

                if d_start <= reg_date_only <= d_end:
                    if search_all and search_all.lower() not in e.lower() and search_all.lower() not in row['Աշխատակից'].lower():
                        continue

                    all_logs.append({
                        'display_date': reg_dt_str, 
                        'reg_dt_obj': reg_dt_obj,
                        'incident_date': parts[0], 
                        'worker': row['Աշխատակից'], 
                        'dept': row['Ստորաբաժանում'],
                        'type': parts[1], 'link': parts[2], 'desc': parts[3],
                        'status': parts[4], 'boss_comm': parts[5] if len(parts) > 5 else "-",
                        'p_idx': p_idx, 'e_idx': e_idx
                    })

        # ՍՈՐՏԱՎՈՐՈՒՄ (Նորերը վերևում)
        all_logs.sort(key=lambda x: x['reg_dt_obj'], reverse=True)

        if not all_logs:
            st.info("Նշված ժամանակահատվածում գրառումներ չկան:")
        else:
            # --- ԷՔՍՊՈՐՏ EXCEL ---
            export_data = []
            for l in all_logs:
                export_data.append({
                    "Գրանցման Ամսաթիվ": l['display_date'],
                    "Խախտման Ամսաթիվ": l['incident_date'],
                    "Աշխատակից": l['worker'],
                    "Բաժին": l['dept'],
                    "Խախտման Տեսակ": l['type'],
                    "Կարգավիճակ": l['status'],
                    "Նկարագրություն": l['desc'],
                    "Մեկնաբանություն": l['boss_comm']
                })
            
            df_export = pd.DataFrame(export_data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='History')
            
            st.download_button(
                label="📥 Արտահանել Excel (Ֆիլտրված)",
                data=output.getvalue(),
                file_name=f"prod_history_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- ՑՈՒՑԱԴՐՈՒՄ ---
            for log in all_logs:
                msg = f"📅 {log['display_date']} | 👔 {log['worker']} — {log['status']}"
                if log['status'] == "Սպասվում է": st.info(msg)
                elif log['status'] == "Ոչ մի խնդիր": st.success(msg)
                elif log['status'] == "Նկատողություն": st.warning(msg)
                else: st.error(msg)

                with st.expander("Մանրամասն"):
                    st.write(f"**Բաժին:** {log['dept']} | **Տեսակ:** {log['type']}")
                    st.write(f"**Խախտման օր:** {log['incident_date']} | **Ուղի:** `{log['link']}`")
                    
                    if log['link']:
                        if st.button(f"📂 Բացել ֆայլը", key=f"f_all_{log['p_idx']}_{log['e_idx']}"):
                            f_path = log['link'].strip()
                            if os.path.exists(f_path):
                                if os.name == 'nt': os.startfile(f_path)
                                else: subprocess.call(['open', f_path])
                            else: st.error(f"Ֆայլը չի գտնվել")

                    st.write(f"**Նկարագրություն:** {log['desc']}")
                    st.divider()
                    
                    u_key = f"upall_{log['p_idx']}_{log['e_idx']}"
                    status_options = ["Սպասվում է", "Ոչ մի խնդիր", "Նկատողություն", "Տուգանք"]
                    curr_idx = status_options.index(log['status']) if log['status'] in status_options else 0

                    new_st = st.selectbox("Կարգավիճակ", status_options, index=curr_idx, key=f"s_all_{u_key}")
                    new_cm = st.text_input("Մեկնաբանություն", value=log['boss_comm'], key=f"c_all_{u_key}")
                    
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("💾 Պահպանել", key=f"save_all_{u_key}", use_container_width=True):
                            c_df = pd.read_csv(PROD_DB_FILE).fillna("")
                            ent = [e for e in str(c_df.at[log['p_idx'], 'Պատմություն']).split('; ') if e]
                            p = [i.strip() for i in ent[log['e_idx']].split(' | ')]
                            while len(p) < 7: p.append("-")
                            p[4], p[5] = new_st, (new_cm if new_cm else "-")
                            ent[log['e_idx']] = " | ".join(p)
                            c_df.at[log['p_idx'], 'Պատմություն'] = "; ".join(ent) + "; "
                            c_df.to_csv(PROD_DB_FILE, index=False)
                            # Սինխրոնացում (Թարմացնում ենք գլխավոր df-ը)
                            df_prod = c_df.copy()
                            st.rerun()

                    with b2:
                        if st.session_state.get('user_role') == 'admin':
                            if st.button("🗑️ Հեռացնել", key=f"del_all_{u_key}", use_container_width=True):
                                c_df = pd.read_csv(PROD_DB_FILE).fillna("")
                                ent = [e for e in str(c_df.at[log['p_idx'], 'Պատմություն']).split('; ') if e]
                                if 0 <= log['e_idx'] < len(ent):
                                    ent.pop(log['e_idx'])
                                    c_df.at[log['p_idx'], 'Պատմություն'] = "; ".join(ent) + ("; " if ent else "")
                                    c_df.to_csv(PROD_DB_FILE, index=False)
                                    # ՍԻՆԽՐՈՆԱՑՈՒՄ. Այս տողը կարևոր է, որպեսզի բլոկ 5-ում ևս անհետանա
                                    df_prod = c_df.copy()
                                    st.rerun()
    else:
        st.warning("Խնդրում ենք ընտրել ժամանակահատվածի ավարտի ամսաթիվը:")