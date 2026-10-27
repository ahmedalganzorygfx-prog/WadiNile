import os, re, sqlite3, unicodedata
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv('DATABASE_PATH', str(BASE_DIR / 'wadi_nile.db')))
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-key-before-publishing')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'WadiNile@2026')
CATEGORIES = ['الكل','الشوربات','الساندوتشات','الوجبات','الطواجن','الأسماك','الجمبري والسي فود','أرز وادي النيل','السلطات','المكرونات','المشروبات']
BRANCHES = [
 {'name':'فرع المهندسين','address':'82 شارع وادي النيل - المهندسين'},
 {'name':'فرع حدائق الأهرام','address':'حدائق الأهرام - الجيزة'},
 {'name':'فرع طريق الواحات','address':'طريق الواحات - 6 أكتوبر'},
 {'name':'فرع محور 26 يوليو','address':'أمام مول المرشدي - 6 أكتوبر'},
 {'name':'فرع الساحل الشمالي','address':'قرية قرطاج - الكيلو 81'},
]
PHOTO_DIR = BASE_DIR / 'assets' / 'facebook_photos'
ALLOWED = {'.jpg','.jpeg','.jfif','.png','.webp'}

def db():
    c=sqlite3.connect(DB_PATH, timeout=20)
    c.row_factory=sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS menu_items(id INTEGER PRIMARY KEY AUTOINCREMENT,category TEXT NOT NULL,name TEXT NOT NULL,description TEXT DEFAULT '',price REAL NOT NULL DEFAULT 0,image_url TEXT DEFAULT '',active INTEGER NOT NULL DEFAULT 1)''')
        c.execute('''CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_name TEXT NOT NULL,phone TEXT NOT NULL,branch TEXT DEFAULT '',order_details TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

def norm(s):
    s=unicodedata.normalize('NFKC',str(s or '')).lower()
    s=re.sub(r'[ً-ٰٟـ]','',s).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ة','ه')
    return ' '.join(re.sub(r'[^a-z0-9؀-ۿ]+',' ',s).split())

def photo_for(name, image_url=''):
    # Prefer a user-specified image URL, otherwise match named local Facebook photos conservatively.
    if image_url and image_url.strip(): return image_url.strip()
    words=[w for w in norm(name).split() if len(w)>2 and w not in {'كيلو','جرام','جم','مخصوص','طبق','وجبه','طازج','طازجه'}]
    best=None; score=0
    if PHOTO_DIR.exists():
        for p in PHOTO_DIR.iterdir():
            if p.suffix.lower() not in ALLOWED: continue
            stem=norm(p.stem)
            if not stem or re.search(r'(^| )\d{5,}',stem): continue
            sc=sum(1 for w in words if w in stem)
            if sc>score: best,score=p,sc
    if best and (score>=2 or (len(words)==1 and words[0] in norm(best.stem))):
        return url_for('static_photo', filename=best.name)
    # Avoid displaying an unrelated dish when there is no confident filename match.
    return url_for('static',filename='img/seafood-placeholder.svg')

@app.route('/facebook-photos/<path:filename>')
def static_photo(filename):
    from flask import send_from_directory
    return send_from_directory(PHOTO_DIR, filename)

def all_items(category='الكل', search=''):
    sql='SELECT * FROM menu_items WHERE active=1'; args=[]
    if category and category!='الكل': sql+=' AND category=?'; args.append(category)
    if search:
        sql+=' AND (name LIKE ? OR description LIKE ?)'; args += [f'%{search}%',f'%{search}%']
    sql+=' ORDER BY category, name'
    rows=[]
    with db() as c: rows=c.execute(sql,args).fetchall()
    return [dict(r, display_image=photo_for(r['name'],r['image_url'])) for r in rows]

def admin_required(fn):
    @wraps(fn)
    def inner(*a,**kw):
        if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
        return fn(*a,**kw)
    return inner

@app.context_processor
def globals_for_templates():
    return {'categories':CATEGORIES[1:],'branches':BRANCHES,'cart_count':sum(int(v) for v in session.get('cart',{}).values())}

@app.route('/')
def home():
    items=all_items()[:8]
    photos=[]
    if PHOTO_DIR.exists():
        photos=[url_for('static_photo',filename=p.name) for p in sorted(PHOTO_DIR.iterdir()) if p.suffix.lower() in ALLOWED][:12]
    return render_template('index.html',items=items,photos=photos)

@app.route('/menu')
def menu():
    category=request.args.get('category','الكل')
    if category not in CATEGORIES: category='الكل'
    search=request.args.get('q','').strip()
    return render_template('menu.html',items=all_items(category,search),selected=category,search=search)

@app.route('/cart/add/<int:item_id>',methods=['POST'])
def cart_add(item_id):
    with db() as c: item=c.execute('SELECT id FROM menu_items WHERE id=? AND active=1',(item_id,)).fetchone()
    if not item: flash('هذا الصنف غير متاح حاليًا.','error'); return redirect(request.referrer or url_for('menu'))
    cart=session.get('cart',{}); key=str(item_id); cart[key]=min(int(cart.get(key,0))+1,99); session['cart']=cart
    flash('تمت إضافة الصنف إلى السلة.','success')
    return redirect(request.referrer or url_for('menu'))

@app.route('/cart')
def cart():
    cart_data=session.get('cart',{}); ids=[int(i) for i in cart_data]
    items=[]; total=0
    if ids:
        marks=','.join('?' for _ in ids)
        with db() as c: rows=c.execute(f'SELECT * FROM menu_items WHERE active=1 AND id IN ({marks})',ids).fetchall()
        for r in rows:
            d=dict(r); d['qty']=int(cart_data.get(str(r['id']),1)); d['display_image']=photo_for(r['name'],r['image_url']); d['subtotal']=d['price']*d['qty']; total+=d['subtotal']; items.append(d)
    return render_template('cart.html',items=items,total=total)

@app.post('/cart/update')
def cart_update():
    cart=session.get('cart',{})
    for key in list(cart):
        try: qty=int(request.form.get('qty_'+key,'0'))
        except ValueError: qty=0
        if qty<=0: cart.pop(key,None)
        else: cart[key]=min(qty,99)
    session['cart']=cart; return redirect(url_for('cart'))

@app.route('/checkout',methods=['GET','POST'])
def checkout():
    cart_data=session.get('cart',{}); ids=[int(i) for i in cart_data]
    if request.method=='POST':
        name=request.form.get('name','').strip(); phone=request.form.get('phone','').strip(); branch=request.form.get('branch','').strip(); address=request.form.get('address','').strip(); notes=request.form.get('notes','').strip()
        if not name or not phone or not ids:
            flash('يرجى إدخال الاسم ورقم الهاتف وإضافة أصناف للسلة.','error'); return redirect(url_for('checkout'))
        marks=','.join('?' for _ in ids)
        with db() as c: rows=c.execute(f'SELECT * FROM menu_items WHERE active=1 AND id IN ({marks})',ids).fetchall()
        lines=[]; total=0
        for r in rows:
            qty=int(cart_data.get(str(r['id']),1)); sub=r['price']*qty; total+=sub; lines.append(f"{r['name']} × {qty} = {sub:.2f} ج.م")
        details='\n'.join(lines)+f'\nالإجمالي: {total:.2f} ج.م\nالعنوان: {address}\nملاحظات: {notes}'
        with db() as c: c.execute('INSERT INTO orders(customer_name,phone,branch,order_details) VALUES(?,?,?,?)',(name,phone,branch,details))
        session['cart']={}; return render_template('order_success.html',name=name,phone=phone,total=total)
    return render_template('checkout.html',items=all_items_for_cart(cart_data),total=cart_total(cart_data))

def all_items_for_cart(cart_data):
    ids=[int(i) for i in cart_data]
    if not ids:return []
    marks=','.join('?' for _ in ids)
    with db() as c: rows=c.execute(f'SELECT * FROM menu_items WHERE active=1 AND id IN ({marks})',ids).fetchall()
    return [dict(r,qty=int(cart_data.get(str(r['id']),1)),subtotal=r['price']*int(cart_data.get(str(r['id']),1))) for r in rows]
def cart_total(cart_data): return sum(float(x['subtotal']) for x in all_items_for_cart(cart_data))

@app.route('/branches')
def branches_page(): return render_template('branches.html')
@app.route('/about')
def about(): return render_template('about.html')
@app.route('/contact',methods=['GET','POST'])
def contact():
    if request.method=='POST':
        name=request.form.get('name','').strip(); phone=request.form.get('phone','').strip(); message=request.form.get('message','').strip()
        if not name or not phone or not message: flash('يرجى استكمال البيانات.','error')
        else:
            with db() as c: c.execute('INSERT INTO orders(customer_name,phone,branch,order_details) VALUES(?,?,?,?)',(name,phone,'استفسار',message))
            flash('وصلتنا رسالتك، شكرًا لتواصلك.','success'); return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        if request.form.get('username','')==ADMIN_USERNAME and request.form.get('password','')==ADMIN_PASSWORD:
            session['admin_logged_in']=True; return redirect(url_for('admin_dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة.','error')
    return render_template('admin_login.html')
@app.route('/admin/logout')
def admin_logout(): session.clear(); return redirect(url_for('home'))
@app.route('/admin')
@admin_required
def admin_dashboard():
    with db() as c:
        items=c.execute('SELECT * FROM menu_items ORDER BY id DESC').fetchall(); orders=c.execute('SELECT * FROM orders ORDER BY id DESC LIMIT 100').fetchall()
    return render_template('admin.html',items=items,orders=orders)
@app.post('/admin/menu/add')
@admin_required
def admin_add_item():
    category=request.form.get('category','').strip(); name=request.form.get('name','').strip(); desc=request.form.get('description','').strip(); image=request.form.get('image_url','').strip()
    try: price=float(request.form.get('price','0'))
    except ValueError: price=-1
    if category not in CATEGORIES[1:] or not name or price<0: flash('راجع اسم الصنف والقسم والسعر.','error')
    else:
        with db() as c: c.execute('INSERT INTO menu_items(category,name,description,price,image_url,active) VALUES(?,?,?,?,?,1)',(category,name,desc,price,image))
        flash('تمت إضافة الصنف.','success')
    return redirect(url_for('admin_dashboard'))
@app.post('/admin/menu/<int:item_id>/toggle')
@admin_required
def admin_toggle(item_id):
    with db() as c: c.execute('UPDATE menu_items SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?',(item_id,))
    flash('تم تحديث حالة الصنف.','success'); return redirect(url_for('admin_dashboard'))
@app.post('/admin/orders/<int:order_id>/delete')
@admin_required
def admin_delete_order(order_id):
    with db() as c: c.execute('DELETE FROM orders WHERE id=?',(order_id,))
    flash('تم حذف الطلب.','success'); return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def not_found(e): return render_template('404.html'),404

init_db()
if __name__=='__main__': app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=False)
