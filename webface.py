from decimal import DivisionByZero
from flask import Flask, render_template, request, redirect, url_for, session, flash
import functools
from mysqlite import SQLite
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import string
import re

app = Flask(__name__)
app.secret_key = b"totoj e zceLa n@@@hodny retezec nejlep os.urandom(24)"
app.secret_key = b"x6\x87j@\xd3\x88\x0e8\xe8pM\x13\r\xafa\x8b\xdbp\x8a\x1f\xd41\xb8"


slova = ("Super", "Perfekt", "Úža", "Flask")


@app.route("/", methods=["GET"])
def index():
    return render_template("base.html")

def prihlasit(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if "user" in session:
            return function(*args, **kwargs)
        else:
            return redirect(url_for("login", url=request.path))

    return wrapper


@app.route("/zkracovač/",  methods=["GET"])
def zkracovač():
    new = request.args.get("new")
    if "uzivatel" in session:
        with SQLite("data.db") as cur:
            res = cur.execute("SELECT zkratka, adresa FROM adresy Where user=?", [session["uzivatel"]])
            zkratky = res.fetchall()
            if not zkratky:
                zkratky = []
    else:
        zkratky = []
    return render_template("zkracovač.html", new=new, zkratky=zkratky)



@app.route("/zkracovač/", methods=["POST"])
def zkracovač_post():
    url = request.form.get("url")
    if url and re.match("https?://.+", url):
        zkratka = ''.join(random.choices(string.ascii_uppercase +
                                string.digits, k=5))

        with SQLite("data.db") as cur:
            if "uzivatel" in session:
                cur.execute("INSERT INTO adresy (zkratka, adresa, user) VALUES (?, ?, ?)", [zkratka, url, session["uzivatel"]])
                flash("Adresa uložena")
            else:
                cur.execute("INSERT INTO adresy (zkratka, adresa) VALUES (?, ?)", [zkratka, url])
            return redirect(url_for("zkracovač", new=zkratka))
    else:
        flash("To, co jsi zadal není adresa webové stránky!")


    return redirect(url_for("zkracovač",))

@app.route("/zkracovač/<zkratka>",  methods=["GET"])
def dezkracovac(zkratka):
    print(zkratka)
    with SQLite("data.db") as cur:
        cur.execute("SELECT adresa FROM adresy WHERE zkratka=? ;", [zkratka])
        odpoved = cur.fetchone()
        print(type(odpoved))
        if odpoved:
            print(odpoved[0])
            return redirect(odpoved[0])

        else:
            flash("Toto ({}) není korektní ZKRATKA".format(zkratka))


    return redirect(url_for("zkracovač"))



@app.route("/info/")
def info():
    return render_template("info.html")


@app.route("/abc/")
def abc():
    if 'uzivatel' not in session:
        flash("Nejsi prihlasen blazne", "error")
        return redirect(url_for("login", page = request.full_path))
    return render_template("abc.html", slova=slova)




@app.route("/malina/", methods=['GET', 'POST'])
def malina():
    if 'uzivatel' not in session:
        flash("Nejsi prihlasen blazne", "error")
        return redirect(url_for("login", page = request.full_path))

    hmotnost = request.args.get('hmotnost')
    vyska = request.args.get('vyska')

    print(hmotnost, vyska)    
    if hmotnost and vyska:
        try:
                hmotnost = float(hmotnost)
                vyska=float(vyska)
                bmi = hmotnost/(0.01*vyska)**2
        except (DivisionByZero, ValueError):
                bmi = None
    else:
        bmi = None

    return render_template('malina.html', bmi=bmi)


@app.route("/login/", methods=['GET'])
def login():
    jmeno = request.args.get('jmeno')
    heslo = request.args.get('heslo')
    print(jmeno,heslo)
    return render_template('login.html')

@app.route("/login/", methods=['POST'])
def login_post():
    jmeno = request.form.get('jmeno')
    heslo = request.form.get('heslo')
    page = request.args.get("page")

    with SQLite("data.db") as cur:
        cur.execute("SELECT passwd FROM user WHERE login = ? ", [jmeno] )
        ans = cur.fetchall()
      

    if ans and check_password_hash(ans[0][0], heslo):
        flash("jsi přihlašen", "message")
        session["uzivatel"] = jmeno
        if page:
            return redirect(page)   
    else:
        flash("nespravne udaje", "error")
    if page:
        return redirect(url_for("login", page= page)) 
    return redirect(url_for('login'))


@app.route("/logout/", methods=['GET','POST'])
def logout():
    session.pop("uzivatel", None)
    return redirect(url_for('index'))

@app.route("/registrace/", methods=['GET'])
def registrace():
    return render_template('registrace.html')

@app.route("/registrace/", methods=['POST'])
def registrace_post():
    jmeno = request.form.get('jmeno')
    heslo = request.form.get('heslo')
    heslo2 = request.form.get('heslo2')
    
    if not (jmeno and heslo and heslo2):
        flash('Je nutné vyplnit všechna políčka',"error")

    if heslo != heslo2:
        flash('Hesla nejsou stejná',"error")
    
    heslohash = generate_password_hash(heslo)
    try:
        with SQLite("data.db") as cur:
            cur.execute( " INSERT INTO user (login,passwd) VALUES (?,?) ", [jmeno,heslohash] )
            ans = cur.fetchall()
            flash("přihlášen")
            flash("Zaregistrováno")
            session["uzivatel"] = jmeno
            return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        flash(f"Jméno {jmeno} je již zabrané ")   


    return redirect(url_for('registrace'))

