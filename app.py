import os, sqlite3, base64
from pathlib import Path
from datetime import datetime
import streamlit as st

BASE = Path(__file__).resolve().parent
DB = Path(os.getenv('DATABASE_PATH', str(BASE / 'wadi_nile.db')))
LOGO = BASE / 'assets' / 'logo.jpg'
CATEGORIES = ['الشوربات','الساندوتشات','الوجبات','الطواجن','الأسماك','الجمبري والسي فود','أرز وادي النيل','السلطات','المكرونات','المشروبات']
BRANCHES = [
    {'name':'فرع المهندسين','address':'82 شارع وادي النيل - المهندسين'},
    {'name':'فرع حدائق الأهرام','address':'حدائق الأهرام - الجيزة'},
    {'name':'فرع طريق الواحات','address':'طريق الواحات - 6 أكتوبر'},
    {'name':'فرع محور 26 يوليو','address':'أمام مول المرشدي - 6 أكتوبر'},
    {'name':'فرع الساحل الشمالي','address':'قرية قرطاج - الكيلو 81'},
]

def conn_db():
    c=sqlite3.connect(DB, timeout=20); c.row_factory=sqlite3.Row; return c

def init_db():
    with conn_db() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS menu_items (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, name TEXT NOT NULL, description TEXT DEFAULT '', price REAL NOT NULL DEFAULT 0, image_url TEXT DEFAULT '', active INTEGER NOT NULL DEFAULT 1)''')
        c.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL, phone TEXT NOT NULL, branch TEXT DEFAULT '', order_details TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

def query(sql,args=()):
    with conn_db() as c: return c.execute(sql,args).fetchall()
def execute(sql,args=()):
    with conn_db() as c: c.execute(sql,args)

st.set_page_config(page_title='مطاعم أسماك وادي النيل',page_icon='🐟',layout='wide',initial_sidebar_state='expanded')
init_db()
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{--navy:#082f49;--deep:#061f33;--sea:#087e9d;--cyan:#18b7c9;--foam:#eaf8fa;--ink:#19384a;--muted:#66808f;--line:#dce9ed;--gold:#d8ad62}
html,body,[class*="css"],button,input,textarea{font-family:'Cairo',sans-serif!important;direction:rtl}
html,body{direction:rtl;text-align:right}.stApp{background:#f5f9fa;color:var(--ink);direction:rtl}
.block-container{max-width:1420px;padding-top:1.1rem;padding-bottom:2.2rem}
[data-testid="stAppViewContainer"]>.main,[data-testid="stHorizontalBlock"],[data-testid="column"]{direction:rtl}
[data-testid="column"],[data-testid="stMarkdownContainer"],[data-testid="stCaptionContainer"]{text-align:right}
section[data-testid="stSidebar"]{background:#fff;border-left:1px solid var(--line);border-right:0;direction:rtl}section[data-testid="stSidebar"]>div{direction:rtl}
section[data-testid="stSidebar"] [data-testid="stImage"]{padding:8px;border-radius:18px}
section[data-testid="stSidebar"] .stButton>button{background:#f5fafb;color:var(--navy);border:1px solid #e0edf0;text-align:right;direction:rtl;border-radius:13px;padding:12px 16px;font-weight:800;transition:all .2s}
section[data-testid="stSidebar"] .stButton>button:hover{background:#e7f7f9;border-color:#8bd5df;transform:translateX(-2px)}
.hero{position:relative;overflow:hidden;isolation:isolate;background:radial-gradient(circle at 12% 15%,#1ab4c933,transparent 30%),linear-gradient(115deg,#061f33 0%,#073e5b 52%,#087e9d 100%);border-radius:30px;padding:clamp(28px,4vw,58px);color:#fff;box-shadow:0 24px 60px #062e441e;margin:8px 0 30px;border:1px solid #ffffff26;text-align:right}
.hero:before{content:'';position:absolute;z-index:-1;width:310px;height:310px;border:1px solid #ffffff1b;border-radius:50%;left:-95px;bottom:-190px;box-shadow:0 0 0 32px #ffffff08,0 0 0 64px #ffffff06}
.hero:after{content:'وادي النيل';position:absolute;z-index:-1;left:28px;bottom:8px;color:#ffffff0d;font-size:clamp(2rem,5vw,5rem);font-weight:900;transform:rotate(-8deg)}
.hero h1{font-size:clamp(2rem,4vw,3.7rem);font-weight:900;line-height:1.35;margin:7px 0;color:#fff;letter-spacing:-.5px}.hero p{font-size:clamp(1rem,1.5vw,1.25rem);margin:.65rem 0 0;color:#d9f7fb;font-weight:600;line-height:1.9}
.eyebrow{display:inline-block;color:#8feaff;font-weight:900;font-size:1rem;margin-bottom:6px;background:#ffffff12;border:1px solid #ffffff24;border-radius:99px;padding:5px 14px}
h1,h2,h3,h4{color:var(--navy);font-weight:900;letter-spacing:-.2px}.item-card,.branch{background:#fff;border:1px solid var(--line);border-radius:22px;padding:18px;height:100%;box-shadow:0 8px 28px #12324a08}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:#e0ebef!important;border-radius:22px!important;background:#fff;box-shadow:0 9px 28px #103d5108;overflow:hidden}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stImage"] img{border-radius:15px;object-fit:cover}.price{font-size:1.35rem;font-weight:900;color:var(--sea);margin:.3rem 0}
.branch{margin-bottom:12px;line-height:2;border-top:3px solid var(--cyan)}a{color:#087e9d!important;font-weight:800;text-decoration:none!important}a:hover{color:#064b68!important}
div.stButton>button,div.stFormSubmitButton>button{background:linear-gradient(110deg,#087e9d,#13a9bd);color:#fff;border:0;border-radius:13px;font-weight:900;min-height:2.85rem;box-shadow:0 7px 16px #087e9d1b;transition:all .18s}
div.stButton>button:hover,div.stFormSubmitButton>button:hover{background:linear-gradient(110deg,#063c58,#087e9d);color:white;border:0;transform:translateY(-1px)}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);padding:18px;border-radius:18px;box-shadow:0 6px 22px #12324a08;text-align:right}[data-testid="stMetricLabel"],[data-testid="stMetricValue"]{text-align:right;justify-content:flex-start}[data-testid="stMetricValue"]{color:var(--sea);font-weight:900}
[data-testid="stTabs"] [role="tablist"]{direction:rtl;gap:8px}[data-testid="stTabs"] button{font-family:'Cairo',sans-serif;font-weight:800;border-radius:11px;padding:9px 16px}
[data-testid="stForm"]{background:#fff;border:1px solid var(--line);border-radius:20px;padding:20px;direction:rtl}input,textarea{direction:rtl!important;text-align:right!important}[data-baseweb="select"]>div{direction:rtl;text-align:right}[data-testid="stDataFrame"]{direction:rtl}
[data-testid="stAlert"]{direction:rtl;text-align:right;border-radius:14px}hr{border-color:#dceaf0;margin:1.5rem 0}footer{visibility:hidden}
@media(max-width:700px){.hero{padding:26px 22px;border-radius:22px}.hero:after{font-size:2.5rem;left:10px}.hero p{font-size:1rem}.block-container{padding-left:1rem;padding-right:1rem}[data-testid="stHorizontalBlock"]{gap:.6rem}}
</style>''',unsafe_allow_html=True)

if 'cart' not in st.session_state: st.session_state.cart={}
if 'page' not in st.session_state: st.session_state.page='الرئيسية'
if 'admin' not in st.session_state: st.session_state.admin=False

def go(page): st.session_state.page=page
with st.sidebar:
    if LOGO.exists(): st.image(str(LOGO),use_container_width=True)
    st.markdown('<div style="text-align:center;font-weight:900;color:#064b72;font-size:1.2rem">مطاعم أسماك وادي النيل</div><div style="text-align:center;color:#0799c6">البحر بروح مصرية</div>',unsafe_allow_html=True)
    st.divider()
    for p in ['الرئيسية','قائمة الطعام','سلة الطلبات','الفروع','من نحن','تواصل واطلب','لوحة الإدارة']:
        if st.button(p,use_container_width=True,key='nav_'+p): go(p)
    st.caption('نسخة معاينة — يُرجى مراجعة الأسعار وبيانات الفروع قبل النشر الرسمي.')

st.markdown('<div class="hero"><div class="eyebrow">سلسلة مطاعم للمأكولات البحرية</div><h1>مطاعم أسماك وادي النيل</h1><p>البحر بروح مصرية · مذاق بحري يجمع العائلة</p></div>',unsafe_allow_html=True)
page=st.session_state.page

if page in ['الرئيسية','قائمة الطعام']:
    st.markdown('### اكتشف قائمة الطعام' if page=='الرئيسية' else '### قائمة الطعام')
    all_items=query('SELECT * FROM menu_items WHERE active=1 ORDER BY id')
    categories=['الكل']+CATEGORIES
    chosen=st.selectbox('التصنيف',categories,index=0)
    search=st.text_input('ابحث عن صنف',placeholder='اكتب اسم الطبق...')
    items=[dict(x) for x in all_items if (chosen=='الكل' or x['category']==chosen) and search.strip().casefold() in x['name'].casefold()]
    if not items: st.info('لا توجد أصناف مطابقة للبحث.')
    cols=st.columns(3)
    for i,item in enumerate(items):
        with cols[i%3]:
            with st.container(border=True):
                if item['image_url']: st.image(item['image_url'],use_container_width=True)
                st.markdown(f"#### {item['name']}")
                st.caption(item['category'])
                st.write(item['description'] or 'طبق من اختيارات وادي النيل.')
                st.markdown(f"<div class='price'>{item['price']:g} جنيه</div>",unsafe_allow_html=True)
                qty=st.number_input('الكمية',min_value=1,max_value=20,value=1,key=f"qty_{item['id']}")
                if st.button('أضف إلى السلة',key=f"add_{item['id']}",use_container_width=True):
                    k=str(item['id']); st.session_state.cart[k]=st.session_state.cart.get(k,0)+qty; st.success('تمت إضافة الصنف إلى السلة')
    if page=='الرئيسية':
        st.divider(); st.markdown('### فروعنا')
        bcols=st.columns(3)
        for i,b in enumerate(BRANCHES):
            with bcols[i%3]: st.markdown(f"<div class='branch'><b>{b['name']}</b><br>{b['address']}<br><a href='https://www.google.com/maps/search/?api=1&query={b['address']}' target='_blank'>عرض الموقع على خرائط Google</a></div>",unsafe_allow_html=True)
elif page=='سلة الطلبات':
    st.markdown('### سلة الطلبات')
    cart_items=[]; total=0
    for k,q in list(st.session_state.cart.items()):
        rows=query('SELECT * FROM menu_items WHERE id=? AND active=1',(int(k),))
        if rows:
            it=dict(rows[0]); subtotal=it['price']*q; total+=subtotal; cart_items.append((it,q,subtotal))
    if not cart_items: st.info('السلة فارغة. أضف أصنافًا من قائمة الطعام أولًا.')
    else:
        for it,q,sub in cart_items:
            c1,c2,c3=st.columns([4,1,2]); c1.write(it['name']); c2.write(f'× {q}'); c3.write(f'{sub:g} جنيه')
            if st.button('حذف الصنف',key=f"remove_{it['id']}"): st.session_state.cart.pop(str(it['id']),None); st.rerun()
        st.markdown(f'## الإجمالي: {total:g} جنيه')
        with st.form('checkout'):
            name=st.text_input('اسم العميل *'); phone=st.text_input('رقم الهاتف *'); branch=st.selectbox('الفرع', [b['name'] for b in BRANCHES]); notes=st.text_area('العنوان وملاحظات الطلب')
            submitted=st.form_submit_button('تأكيد وإرسال الطلب',use_container_width=True)
        if submitted:
            if not name.strip() or not phone.strip(): st.error('يرجى إدخال الاسم ورقم الهاتف.')
            else:
                details='؛ '.join([f"{it['name']} × {q} = {sub:g} جنيه" for it,q,sub in cart_items])+f' | الإجمالي: {total:g} جنيه | ملاحظات: {notes.strip()}'
                execute('INSERT INTO orders(customer_name,phone,branch,order_details) VALUES(?,?,?,?)',(name.strip(),phone.strip(),branch,details))
                st.session_state.cart={}; st.success('تم تسجيل الطلب. سيتواصل فريق المطعم لتأكيد التفاصيل.'); st.balloons()
elif page=='الفروع':
    st.markdown('### فروع مطاعم أسماك وادي النيل')
    for b in BRANCHES: st.markdown(f"<div class='branch'><h4>{b['name']}</h4>{b['address']}<br><a href='https://www.google.com/maps/search/?api=1&query={b['address']}' target='_blank'>افتح الموقع على خرائط Google</a></div>",unsafe_allow_html=True)
elif page=='من نحن':
    st.markdown('### من نحن')
    st.write('مطاعم أسماك وادي النيل تقدم تجربة للمأكولات البحرية بروح مصرية، مع تشكيلة من الأسماك والجمبري والسي فود والطواجن والوجبات والأطباق الجانبية.')
    st.info('البحر بروح مصرية')
elif page=='تواصل واطلب':
    st.markdown('### تواصل واطلب')
    st.write('الخط الساخن: 19974')
    with st.form('contact_form'):
        name=st.text_input('الاسم *'); phone=st.text_input('رقم الهاتف *'); branch=st.selectbox('الفرع', [b['name'] for b in BRANCHES]); details=st.text_area('تفاصيل الطلب *'); send=st.form_submit_button('إرسال الطلب')
    if send:
        if not name.strip() or not phone.strip() or not details.strip(): st.error('أكمل الاسم ورقم الهاتف وتفاصيل الطلب.')
        else: execute('INSERT INTO orders(customer_name,phone,branch,order_details) VALUES(?,?,?,?)',(name.strip(),phone.strip(),branch,details.strip())); st.success('تم تسجيل الطلب بنجاح.')
elif page=='لوحة الإدارة':
    st.markdown('### لوحة الإدارة')
    if not st.session_state.admin:
        with st.form('admin_login'):
            username=st.text_input('اسم المستخدم'); password=st.text_input('كلمة المرور',type='password'); login=st.form_submit_button('تسجيل الدخول')
        if login:
            if os.getenv('ADMIN_PASSWORD') and username==os.getenv('ADMIN_USERNAME','admin') and password==os.getenv('ADMIN_PASSWORD'):
                st.session_state.admin=True; st.rerun()
            else: st.error('بيانات الدخول غير صحيحة.')
        st.warning('اضبط ADMIN_USERNAME وADMIN_PASSWORD في إعدادات Secrets قبل النشر؛ لوحة الإدارة مغلقة افتراضيًا إذا لم تُضبط كلمة المرور.')
    else:
        if st.button('تسجيل الخروج'): st.session_state.admin=False; st.rerun()
        orders=query('SELECT * FROM orders ORDER BY id DESC LIMIT 200')
        items=query('SELECT * FROM menu_items ORDER BY id DESC')
        a,b,c=st.columns(3); a.metric('إجمالي الطلبات',len(query('SELECT id FROM orders'))); b.metric('الأصناف',len(items)); c.metric('الأصناف النشطة',len(query('SELECT id FROM menu_items WHERE active=1')))
        tab1,tab2=st.tabs(['الطلبات','إدارة المنيو'])
        with tab1:
            if orders:
                st.dataframe([dict(r) for r in orders],use_container_width=True,hide_index=True)
                oid=st.number_input('رقم الطلب المراد حذفه',min_value=1,step=1)
                if st.button('حذف الطلب المحدد'): execute('DELETE FROM orders WHERE id=?',(int(oid),)); st.success('تم الحذف'); st.rerun()
            else: st.info('لا توجد طلبات حتى الآن.')
        with tab2:
            with st.form('add_item'):
                category=st.selectbox('القسم',CATEGORIES); name=st.text_input('اسم الصنف'); desc=st.text_area('الوصف'); price=st.number_input('السعر بالجنيه',min_value=0.0,step=5.0); img=st.text_input('رابط صورة الصنف'); add=st.form_submit_button('إضافة الصنف')
            if add:
                if name.strip(): execute('INSERT INTO menu_items(category,name,description,price,image_url,active) VALUES(?,?,?,?,?,1)',(category,name.strip(),desc.strip(),float(price),img.strip())); st.success('تمت الإضافة'); st.rerun()
            for it in items:
                cc1,cc2,cc3=st.columns([4,2,2]); cc1.write(f"{it['name']} — {it['price']:g} جنيه"); cc2.write('نشط' if it['active'] else 'موقوف')
                if cc3.button('إيقاف' if it['active'] else 'تفعيل',key=f"toggle_{it['id']}"): execute('UPDATE menu_items SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?',(it['id'],)); st.rerun()

st.divider()
st.markdown('<div style="text-align:center;color:#58778b;padding:8px">مطاعم أسماك وادي النيل · البحر بروح مصرية<br>تصميم وتنفيذ احمد الجنزوري</div>',unsafe_allow_html=True)
