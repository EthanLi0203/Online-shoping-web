# encoding: utf-8
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, render_template, g, Response
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from datetime import timedelta
from tools.pgsql_tool import *
from tools.other_tools import *

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


DATABASEURI = "############"

engine = create_engine(DATABASEURI)

engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except Exception as e:
        pass

def execute_add_mod_del(sql, return_id=False):
    g.conn = engine.connect()
    try:
        g.conn.execute(sql)
        if return_id:
            insert_id = g.conn.fetchone()[0]
            g.conn.close()
            return insert_id
        else:
            g.conn.close()
            return True
    except:
        g.conn.close()
        return False


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = get_random_str()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)


@app.route('/signup', methods=["GET","POST"])
def signup():
    if request.method == "GET":
        return render_template('signup.html', title='signup')
    elif request.method == 'POST':
        user_name = request.form.get('username', None)
        pwd = request.form.get('password', None)
        title = 'Signup failed'
        if not pwd or not user_name:
            return render_template('tips.html', tips='Required parameters cannot be empty!', title=title)
        else:
           
            select_sql = """SELECT * FROM "Customer" WHERE username='%s'""" % user_name
            is_exists = g.conn.execute_select(select_sql)
            #is_exists = g.conn.execute(select_sql).fetchall()
            curr_date = get_curr_day()
            
            if not is_exists:
                signup_sql = '''INSERT INTO "Customer" ''' \
                             '''(username, password, create_time)''' \
                             '''VALUES ('%s', '%s', '%s')''' % (user_name, pwd, curr_date)
                if execute_add_mod_del(signup_sql):
                    tips = 'Signup successful.'
                    title = 'Signup successful'
                else:
                    tips = 'Signup failed!'
            else:
                tips = 'User name already exists!'
            return render_template('tips.html', tips=tips, title=title)

@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == 'GET':
        return render_template('login.html', title='login')
    elif request.method == 'POST':
        user_name = request.form.get('username', None)
        pwd = request.form.get('password', None)
        select_sql = """SELECT customer_id,password FROM "Customer" WHERE username='%s'""" % user_name
        res = g.conn.execute_select(select_sql)
        if not res:
            tips = 'user does not exist!'
        else:
            if res[0][1] != pwd:
                tips = 'password error!'
            else:  # Verify login success
                session['login_user'] = user_name
                return redirect(url_for('index', login_user=user_name, title='home page'))
        return render_template('tips.html', tips=tips, title='Login failed')

@app.route('/index')
def index():
    login_user = session.get('login_user', None)
    
    select_sql = '''SELECT key_word,product_fk FROM "HotSearched" WHERE searched_rank <= 10 ORDER BY searched_rank'''
    hot_search_list = g.conn.execute_select(select_sql)
    
    select_sql = '''SELECT product_id, name, price, unit, is_shipfree FROM "Product" WHERE isdelete = false'''
    product_list = g.conn.execute_select(select_sql)
    
    select_sql = '''SELECT DISTINCT b.brand_id, b.brand_name FROM "Brand" b  WHERE EXISTS (SELECT * FROM "Product" p WHERE p.brand_fk=b.brand_id)'''
    brand_list = g.conn.execute_select(select_sql)

    return render_template('index.html', title='home page',login_user=login_user,
                            hot_search_list=hot_search_list, product_list=product_list, brand_list=brand_list)

@app.route('/product/<int:id>')
def detail(id):
    login_user = session.get('login_user', None)
    select_sql = '''SELECT * FROM "Product" WHERE product_id = %s''' % id
    product = g.conn.execute_select(select_sql)[0]
    select_sql = '''SELECT brand_id, brand_name FROM "Brand" WHERE brand_id = %s''' % product[2]
    product_brand = g.conn.execute_select(select_sql)[0]
    select_sql = '''SELECT DISTINCT r.review_content, c.username FROM "Review" r, "Customer" c WHERE r.product_fk = %s AND r.customer_fk=c.customer_id''' % id
    review_list = g.conn.execute_select(select_sql)

    return render_template('detail.html', title=product[3], product=product, product_brand=product_brand,
                           review_list=review_list, login_user=login_user)

@app.route('/customer/address/add', methods=["POST"])
def add_address():
    login_user = session.get('login_user', None)
    if login_user:
        select_sql = '''SELECT customer_id FROM "Customer" WHERE username='%s' ''' % login_user
        u_id = g.conn.execute_select(select_sql)[0][0]
        insert_item = [u_id] + list(request.form.values())
        insert_sql = '''INSERT INTO "Address"(customer_fk, consignee_name, consignee_tel, delivery_address, zipcode, city, country)VALUES (%s, '%s', '%s', '%s', '%s', '%s', '%s');  ''' % \
                     (insert_item[0],insert_item[1], insert_item[2], insert_item[3], insert_item[4], insert_item[5], insert_item[6])
        if execute_add_mod_del(insert_sql):
            return 'ok'
    return ''

@app.route('/customer/address')
def get_address():
    login_user = session.get('login_user', None)
    if login_user:
        select_sql = '''SELECT a.add_id,a.consignee_name,a.consignee_tel,a.delivery_address FROM "Address" a,"Customer" c WHERE a.customer_fk=c.customer_id AND c.username='%s' ''' % login_user
        address_list = g.conn.execute_select(select_sql)
        json_data = {'address_list': []}
        for address in address_list:
            json_data['address_list'].append(list(address))
        return jsonify(json_data)
    else:
        return 'login'
@app.route('/brand/<int:id>')
def brand(id):
    login_user = session.get('login_user', None)
    select_sql = '''SELECT brand_name, brand_brief FROM "Brand" WHERE brand_id = %s''' % id
    brand = g.conn.execute_select(select_sql)[0]
    
    select_sql = '''SELECT product_id, name, price, unit, is_shipfree FROM "Product" WHERE isdelete = false AND brand_fk=%s''' % id
    product_list = g.conn.execute_select(select_sql)
    return render_template('brand.html', title=brand[1], product_list=product_list, brand=brand, login_user=login_user)

@app.route('/center')
def center():
    login_user = session.get('login_user', None)
    if not login_user:
        return redirect(url_for('login', title='login'))
    else:
        select_sql = """SELECT o.order_id,o.amount,o.payment_type FROM "Order" o, "Customer" c WHERE c.customer_id=o.customer_fk AND c.username='%s'""" % login_user
        order_list = g.conn.execute_select(select_sql)
        select_sql = """SELECT a.consignee_name, a.consignee_tel,a.delivery_address,a.zipcode,a.city,a.country 
FROM "Address" a, "Customer" c WHERE a.customer_fk = c.customer_id AND c.username='%s'""" % login_user
        address_list = g.conn.execute_select(select_sql)
        return render_template('center.html', title='center', login_user=login_user, address_list=address_list, order_list=order_list)

@app.route('/order/<int:id>')
def order(id):
    login_user = session.get('login_user', None)
    if not login_user:
        return redirect(url_for('login', title='login'))
    else:
        
        verification_sql = '''SELECT o.order_id FROM "Order" o, "Customer" c WHERE o.order_id = %s AND c.username= '%s' AND o.customer_fk=c.customer_id''' % (id, login_user)
        if g.conn.execute_select(verification_sql):
            select_sql = '''SELECT p.product_id,p.name,p.price,p.unit,orp.num FROM "OrderRelationProduct" orp, "Product" p  WHERE orp.order_fk=%s AND orp.product_fk=p.product_id''' % id
            order_products = g.conn.execute_select(select_sql)
            return render_template('order.html', title='order', login_user=login_user, order_products=order_products)
        else:
            return render_template('tips.html', tips='You have no jurisdiction.')

@app.route('/signout')
def sign_out():
    login_user = session.get('login_user', None)
    if login_user:
        session.pop('login_user')
    return redirect(url_for('login', title='login'))

@app.route('/search')
def search():
    keys = request.args.get('keys', None)
    select_sql = '''SELECT product_id, name, price, unit, is_shipfree FROM "Product" WHERE isdelete = false AND LOWER(name) LIKE '%{}%' '''.format(keys.lower())
    res = g.conn.execute_select(select_sql)
    json_data = {'products': []}
    for product in res:
        json_data['products'].append(list(product))
    return jsonify(json_data)

@app.route('/pay', methods=["POST"])
def pay():
    login_user = session.get('login_user', None)
    if login_user:
        select_sql = '''SELECT customer_id FROM "Customer" WHERE username='%s' ''' % login_user
        u_id = g.conn.execute_select(select_sql)[0][0]
        product_id = request.form.get('product_id')
        num = int(request.form.get('num'))
        product_price = float(request.form.get('product_price'))
        pay_func = request.form.get('pay_func')
        add_id = request.form.get('add_id')
        insert_sql = ''' INSERT INTO "Order"(customer_fk, add_fk, amount, payment_type) VALUES (%s, %s, %s, '%s') returning order_id''' % (u_id, add_id, product_price*num, pay_func)
        last_insert_row_id = execute_add_mod_del(insert_sql, return_id=True)

        update_sql = '''UPDATE "Product" SET goods_num=goods_num-%s, sold_num=sold_num+%s WHERE product_id=%s;''' % (num, num, product_id)
        execute_add_mod_del(update_sql)
        insert_sql = ''' INSERT INTO "OrderRelationProduct"(product_fk, order_fk, num) VALUES (%s, %s, %s)''' % (product_id, last_insert_row_id,num)
        execute_add_mod_del(insert_sql)
        return render_template('tips.html', tips='Successful payment')
    else:
        return redirect(url_for('login', title='login'))

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
