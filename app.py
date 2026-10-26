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
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800;900&display=swap');
html,body,[class*="css"]{font-family:'Tajawal',sans-serif;direction:rtl}
.stApp{background:#f5f9fc;color:#12324a}.block-container{max-width:1300px;padding-top:1.1rem}
section[data-testid="stSidebar"]{background:#eaf4fa;border-left:1px solid #d7e7f1}
.hero{background:linear-gradient(120deg,#063a61,#0879a5);border-radius:24px;padding:28px 32px;color:white;box-shadow:0 12px 30px #063a6120;margin-bottom:22px}
.hero h1{font-size:2.2rem;font-weight:900;margin:0}.hero p{font-size:1.15rem;margin:.35rem 0 0;color:#c8f2ff}
.eyebrow{color:#00a4d6;font-weight:800;letter-spacing:.4px}.item-card{background:white;border:1px solid #dceaf2;border-radius:18px;padding:14px;height:100%;box-shadow:0 5px 18px #12324a0a}
.price{font-size:1.15rem;font-weight:900;color:#007da8}.branch{background:white;border:1px solid #dceaf2;border-radius:15px;padding:16px;margin-bottom:8px}
div.stButton>button,div.stFormSubmitButton>button{background:#087da8;color:white;border:0;border-radius:10px;font-weight:800;min-height:2.5rem}
div.stButton>button:hover,div.stFormSubmitButton>button:hover{background:#075a7c;color:white}
[data-testid="stMetric"]{background:white;border:1px solid #dceaf2;padding:12px;border-radius:14px}
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

st.markdown('<div class="hero"><div class="eyebrow" style="color:#8fe8ff">سلسلة مطاعم</div><h1>مطاعم أسماك وادي النيل</h1><p>البحر بروح مصرية · مذاق بحري يجمع العائلة</p></div>',unsafe_allow_html=True)
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
            if username==os.getenv('ADMIN_USERNAME','admin') and password==os.getenv('ADMIN_PASSWORD','WadiNile@2026'):
                st.session_state.admin=True; st.rerun()
            else: st.error('بيانات الدخول غير صحيحة.')
        st.warning('قبل النشر العام غيّر بيانات دخول الإدارة من إعدادات الاستضافة.')
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
