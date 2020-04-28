import os
from flask import Flask, request, render_template, url_for, send_from_directory, jsonify, redirect, make_response, session, flash
from werkzeug import secure_filename
from flask_session import Session
from app import app
import datetime
import sqlite3
import sys
import json
from flask_bcrypt import Bcrypt
from flask_bcrypt import check_password_hash 
from tzlocal import get_localzone
import datetime
from pytz import timezone
from bs4 import BeautifulSoup


f = 0
name_aricle = 0
title_article = 0
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super key'
sess = Session()
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
UPLOAD_FOLDER = '/home/denis/app/static/video/'
ALLOWED_EXTENSIONS = set(['mp4', 'mpeg', '3g2', '3gp', 'asf'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATABASE = '/home/denis/app/sql/video_anketa.bd'
bcrypt = Bcrypt(app)

@app.route("/cookie/<email>")
def cookie(email):  
    session['email'] = email
    print(session.get('email'))
    return redirect("http://185.3.94.78:5000/Всё")

@app.route("/registation", methods = ["GET", "POST"])
def regist():
    if session.get('email') != None:
        return redirect("http://185.3.94.78:5000/download")

    if request.method == "GET":
        return render_template("registation.html")

    name_surname = request.form["name_surname"]
    email = request.form["email"]
    password = request.form["pass"]
    agree = request.form.getlist("agree")

    print(name_surname,email,password)

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    print(pw_hash)

    if not name_surname or not password or not email or agree[0] != "on":
        return render_template("registation.html", alert = "Введите данные!")
    
    #добавляем записи в таблицу
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("INSERT INTO registration (email,name_surname,password) VALUES (?, ?, ?)", (email,name_surname,pw_hash))
        con.commit()
        rc = cur.fetchall()
        print(rc)
        return redirect("http://185.3.94.78:5000/cookie/" + str(email))

@app.route("/come_in", methods = ["GET", "POST"])
def come_in():
    if session.get('email') != None:
        return redirect("http://185.3.94.78:5000/download")

    if request.method == "GET":
        return render_template("come_in.html")

    email = request.form["email"]
    password = request.form["pass"]

    if not password or not email:
        return render_template("come_in.html", alert = "Введите данные!")

    #добавляем записи в таблицу
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM registration WHERE email = ?", [email])
        rc = cur.fetchall()
        if len(rc) == 0:
            return redirect("http://185.3.94.78:5000/registation")

        check = check_password_hash(rc[0][2], password)
        print(check, rc[0][2])
        if rc[0][0] == email and check == True:
            return redirect("http://185.3.94.78:5000/cookie/" + str(email))
        else:
            return redirect("http://185.3.94.78:5000/registation")



def allowed_file(filename):
    return filename[-3:].lower() in ALLOWED_EXTENSIONS

@app.route("/download", methods=["GET", "POST"])
def upload_file():
    print(session.get('email'))
    if session.get('email') == None:
        return redirect("http://185.3.94.78:5000/come_in")

    if request.method == "GET":
        return render_template("site_download_video.html")

    file = request.files["file"]

    if not allowed_file(file.filename):
        return

    channel_name = request.form["channel_name"]
    headline = request.form["headline"]
    topic = request.form["topic"]
    description = request.form["description"]

    if not channel_name or not headline or not description or not file:
        return render_template("site_download_video.html", alert = "Введите данные!")
    
    print('**found file', file.filename)
    filename = secure_filename(file.filename)
    print(filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("INSERT INTO videos (id, channel_name, topic, headline, description, views) VALUES (?, ?, ?, ?, ?, ?)", (filename, channel_name, topic, headline, description, 0))
        con.commit()
        return redirect('http://185.3.94.78:5000/watch/' + str(file.filename))


@app.route('/watch/<filename>')
def uploaded_file(filename):
    if session.get('email') != None:
        come_in = True
    elif session.get('email') == None:
        come_in = False

    fname = filename
    filename = '/static/video/' + str(filename)
    filename = str(filename)

    #SQL
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM videos WHERE id = ?", [fname])
        rc = cur.fetchall()
        global f
        f = fname
        print(rc)
        visit = int(rc[0][4])
        visit += 1

        channel = rc[0][1]
        cur.execute("SELECT COUNT(*) FROM subscriptions WHERE channel = ?", [channel])
        cr = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM likes WHERE channel = ?", [channel])
        cr1 = cur.fetchall()
    
        cur.execute("SELECT COUNT(*) FROM dislikes WHERE channel = ?", [channel])
        cr2 = cur.fetchall()

        cur.execute("UPDATE videos SET views = ? WHERE views = ?", (visit, rc[0][4]))
        print(rc)
        return render_template("site.html", 
            visits = rc[0][4],
            filename = filename,
            channel_name = rc[0][1],
            headline = rc[0][2], 
            description = rc[0][3], 
            subs = cr[0][0],
            likes = cr1[0][0], 
            dislikes = cr2[0][0],
            come_in = come_in)


@app.route("/subscribe", methods=["POST"])
def subscribe():
    if session.get('email') == None:
        return redirect("http://185.3.94.78:5000/come_in")

    print("video_id: ", request.form["video_id"])
    global f
    sensor_subsript = 0
    email = session.get('email')

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM videos WHERE id = ?", [f])
        rc = cur.fetchall()
        print(rc[0][1], email)
        channel = rc[0][1]
        id_table = str(email) + str(channel)
        cur.execute("SELECT user, channel, COUNT(*) FROM subscriptions group by user, channel having count(*)")
        cr = cur.fetchall()
        if len(cr) == 0:
            cur.execute("INSERT INTO subscriptions (id, user, channel) VALUES (?, ?, ?)", (id_table ,email, channel))
            con.commit()
            sensor_subsript += 1
        if sensor_subsript == 0:
            if cr[0][2] == 1:
                id_table = str(cr[0][0]) + str(cr[0][1])
                print(id_table)
                cur.execute("DELETE FROM subscriptions WHERE id = ?", [id_table])
                con.commit()
        print(sensor_subsript)
        print(cr)
        cur.execute("SELECT COUNT(*) FROM subscriptions WHERE channel = ?", [channel])
        rc = cur.fetchall()
        print(rc)

        return jsonify({
            "ok": True,
            "subs": rc,
        })

@app.route("/like", methods=["POST"])
def like():
    if session.get('email') == None:
        return redirect("http://185.3.94.78:5000/come_in")

    print("video_id: ", request.form["video_id"])
    global f
    email = session.get('email')
    sensor_like = 0

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM videos WHERE id = ?", [f])
        rc = cur.fetchall()
        print(rc[0][1], email)
        channel = rc[0][1]
        id_table = str(email) + str(channel)
        cur.execute("SELECT user, channel, COUNT(*) FROM likes group by user, channel having count(*)")
        cr = cur.fetchall()
        if len(cr) == 0:
            cur.execute("INSERT INTO likes (id, user, channel) VALUES (?, ?, ?)", (id_table ,email, channel))
            con.commit()
            sensor_like += 1
            
        if sensor_like == 0:
            if cr[0][2] == 1:
                id_table = str(cr[0][0]) + str(cr[0][1])
                print(id_table)
                cur.execute("DELETE FROM likes WHERE id = ?", [id_table])
                con.commit()   
        
        print(cr)
        cur.execute("SELECT COUNT(*) FROM likes WHERE channel = ?", [channel])
        rc = cur.fetchall()
        print(rc)

        return jsonify({
            "ok": True,
            "like": rc,
        })

@app.route("/dislike", methods=["POST"])
def dislike():
    if session.get('email') == None:
        return redirect("http://185.3.94.78:5000/come_in")

    print("video_id: ", request.form["video_id"])
    global f
    email = session.get('email')
    sensor_dislike = 0

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM videos WHERE id = ?", [f])
        rc = cur.fetchall()
        print(rc[0][1], email)
        channel = rc[0][1]
        id_table = str(email) + str(channel)
        cur.execute("SELECT user, channel, COUNT(*) FROM dislikes group by user, channel having count(*)")
        cr = cur.fetchall()
        print(cr)
        if len(cr) == 0:
            cur.execute("INSERT INTO dislikes (id, user, channel) VALUES (?, ?, ?)", (id_table ,email, channel))
            con.commit()
            sensor_dislike += 1

        if sensor_dislike == 0:
            if cr[0][2] == 1:
                id_table = str(cr[0][0]) + str(cr[0][1])
                print(id_table)
                cur.execute("DELETE FROM dislikes WHERE id = ?", [id_table])
                con.commit()

        cur.execute("SELECT COUNT(*) FROM dislikes WHERE channel = ?", [channel])
        rc = cur.fetchall()
        print(rc)

        return jsonify({
            "ok": True,
            "dis": rc,
        })

@app.route("/download_article", methods = ["GET", "POST"])
def download_article():
    if session.get('email') == None:
        return redirect("http://185.3.94.78:5000/come_in")

    if request.method == "GET":
        return render_template("download_article.html")

    global blog
    name = request.form["name"]
    email = session.get('email') 
    topic = request.form["topic"]
    article = request.form["article"]
    blog = article
    agree = request.form.getlist("agree")
    print(name, email, topic, article, agree)

    if not name or not topic or not article or agree[0] != "on":
        return render_template("download_article", alert = "Введите данные")

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM registration WHERE email = ?", [email])
        rc = cur.fetchall()
        author = rc[0][1]
        cur.execute("INSERT INTO  article (name, topic, article, views, author) VALUES (?, ?, ?, ?, ?)", (name, topic, article, 0, author))
        con.commit()
        cur.execute("SELECT * FROM article WHERE name = ?", [name])
        rc = cur.fetchall()
        print(rc)
        return redirect("http://185.3.94.78:5000/article/" + str(rc[0][0]))

@app.route("/inf", methods = ["GET", "POST"])
def inf():
    return render_template("privacy.html")

@app.route("/article/<name>", methods = ["GET", "POST"])
def article(name):
    if session.get('email') != None:
        come_in = True
    elif session.get('email') == None:
        come_in = False

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM article WHERE name = ?", [name])
        rc = cur.fetchall()
        print(rc)
        global title_article
        global name_aricle
        name_aricle = name
        title_article = rc[0][0]
        topic = rc[0][1]
        views = rc[0][3]
        name_user = rc[0][4]
        views += 1

        cur.execute("UPDATE article SET views = ? WHERE views = ? and name = ?", (views, rc[0][3], name))

        cur.execute("SELECT COUNT(*) FROM likes_article WHERE blog = ?", [name])
        like = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM dislikes_article WHERE blog = ?", [name])
        dislike = cur.fetchall()

        cur.execute('SELECT COUNT(*) FROM comment WHERE title_article = ?', [title_article])
        rcom = cur.fetchall()
        print(rcom)
        array_com = []
        for i in range(rcom[0][0]):
            cur.execute('SELECT * FROM comment WHERE title_article = ?', [title_article])
            ccom = cur.fetchall()
            html_usename = '<p style="font-size:13px; color:#414B50; background-color:#BFCAE2;">' + str(ccom[i][1]) + " "+ str(ccom[i][3]) + "</p>"
            array_com.insert(0, html_usename)
            html_com = '<p>' + str(ccom[i][0]) + "</p><br>"
            array_com.insert(1, html_com)

        com = " ".join(array_com)

        return render_template("article.html", 
            name = name, 
            name_user = name_user, 
            topic = topic,
            article = rc[0][2],
            likes = like[0][0],
            dislikes = dislike[0][0],
            comment = com,
            views = views,
            come_in = come_in)


@app.route("/like_article", methods=["POST"])
def like_article():
    print("video_id: ", request.form["video_id"])
    email = session.get('email')
    sensor_like = 0
    global name_aricle
    name = name_aricle

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()

        id_table = str(email) + str(name)
        cur.execute("SELECT user, blog, COUNT(*) FROM likes_article group by user, blog having count(*)")
        cr = cur.fetchall()
        if len(cr) == 0:
            cur.execute("INSERT INTO likes_article (id, user, blog) VALUES (?, ?, ?)", (id_table ,email, name))
            con.commit()
            sensor_like += 1
            
        if sensor_like == 0:
            if cr[0][2] == 1:
                id_table = str(cr[0][0]) + str(cr[0][1])
                print(id_table)
                cur.execute("DELETE FROM likes_article WHERE id = ?", [id_table])
                con.commit()   
        
        print(cr)
        cur.execute("SELECT COUNT(*) FROM likes_article WHERE blog = ?", [name])
        rc = cur.fetchall()
        print(rc)

        return jsonify({
            "ok": True,
            "likes": rc,
        })

@app.route("/dislike_article", methods=["POST"])
def dislike_article():
    print("video_id: ", request.form["video_id"])
    email = session.get('email')
    sensor_like = 0
    global name_aricle
    name = name_aricle

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        id_table = str(email) + str(name)
        cur.execute("SELECT user, blog, COUNT(*) FROM dislikes_article group by user, blog having count(*)")
        cr = cur.fetchall()
        if len(cr) == 0:
            cur.execute("INSERT INTO dislikes_article (id, user, blog) VALUES (?, ?, ?)", (id_table ,email, name))
            con.commit()
            sensor_like += 1
            
        if sensor_like == 0:
            if cr[0][2] == 1:
                id_table = str(cr[0][0]) + str(cr[0][1])
                print(id_table)
                cur.execute("DELETE FROM dislikes_article WHERE id = ?", [id_table])
                con.commit()   
        
        print(cr)
        cur.execute("SELECT COUNT(*) FROM dislikes_article WHERE blog = ?", [name])
        rc = cur.fetchall()
        print(rc)

        return jsonify({
            "ok": True,
            "dislikes": rc,
        })

@app.route("/comment", methods=["POST"])
def comment():
    com = request.form["comment"]
    time_zone = request.form["timezone"]
    print(time_zone)
    print(com)
    email = session.get('email')
    global title_article
    print(title_article)

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute('SELECT * FROM registration WHERE email = ?', [email])
        rc = cur.fetchall()
        print(rc)
        username = rc[0][1]
        tz = timezone(time_zone)
        time = datetime.datetime.now(tz)
        time = str(time)
        time = list(time)
        time = time[:16]
        time = "".join(time)
        print(time)
        cur.execute("INSERT INTO comment(comment, user, title_article, time_comment) VALUES(?, ?, ?, ?)", (com , username, title_article, time))
        con.commit()

        cur.execute('SELECT COUNT(*) FROM comment WHERE comment = ?', [com])
        rc = cur.fetchall()
        print(rc)
        array_com = []
        for i in range(rc[0][0]):
            cur.execute('SELECT * FROM comment WHERE title_article = ?', [title_article])
            cr = cur.fetchall()
            html_usename = '<p style="font-size:13px; color:#414B50; background-color:#BFCAE2;">' + str(cr[i][1]) + " " + str(cr[i][3]) + "</p>"
            array_com.insert(0, html_usename)
            html_com = '<p>' + str(cr[i][0]) + "</p><br>"
            array_com.insert(1, html_com)

        com = " ".join(array_com)
        print(com)

        return jsonify({
            "ok": True,
            "comment": com,
        })

@app.route("/<topic_filter>", methods=["GET", "POST"])
def home_article(topic_filter):
    selected_topics = set(['Всё', 'Научтоп', 'IT', 'Искуство', "Природа", "Лучшие"])
    if topic_filter not in selected_topics:
        return render_template('eror_url.html')

    result = {}
    names = []
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM article")
        n = cur.fetchall()
        n = int(n[0][0])
        print(n)
        n -= 1
        headings = {}
        if topic_filter == "Всё":
            cur.execute("SELECT COUNT(*) FROM article")
            rc = cur.fetchall()
            records = rc[0][0]
        else:
            records = 5

        for i in range(records):
            headings["IT"] = ['IT']
            headings['Научтоп'] = ['Physics', 'Mathematics', 'IT', 'Chemistry', 'Historical', 'Philosophy', 'Geographic', 'Saving', 'Biology']
            headings['Искуство'] = ['Art', 'Sculpture', 'Design', 'Painting', 'Music']
            headings['Природа'] = ['Geographic', 'Geological', 'Tourism', 'Hunting', 'Fishing', 'Biology']

            if topic_filter == 'Лучшие':
                cur.execute("SELECT * FROM article ORDER BY views DESC")
                rc = cur.fetchall()
                name = rc[i][0]

            if topic_filter == 'Всё':
                cur.execute("SELECT * FROM article")
                rc = cur.fetchall()
                name = rc[n][0]
            if topic_filter != 'Лучшие' and topic_filter != 'Всё':
                heading = headings[topic_filter]
                print(heading)
                cur.execute("SELECT * FROM article WHERE topic IN (%s) ORDER BY views DESC" % ','.join('?'*len(heading)), heading)
                cr = cur.fetchall()
                name = cr[i][0]

            cur.execute("SELECT * FROM article WHERE name = ?", [name])
            rc = cur.fetchall()
            name_user = rc[0][4]
            topic = rc[0][1]
            views = rc[0][3]
            n -= 1

            cur.execute("SELECT COUNT(*) FROM likes_article WHERE blog = ?", [name])
            like = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM dislikes_article WHERE blog = ?", [name])
            dislike = cur.fetchall()

            array = list(name)
            for i in range(len(array)):
                if array[i] == ' ':
                    array[i] = '%20'

            name_link = ''.join(array)
            print(name_link)
            link_article = "http://185.3.94.78:5000/article/" + str(name_link)
            print(link_article)
            html = rc[0][2]
            raw = BeautifulSoup(html).get_text()
            txt = list(raw)
            a = len(txt) // 10
            print(name)
            while raw[a] != '.':
                a += 1 

            a += 1
            article = raw[:a]
            
            likes = like[0][0]
            dislikes = dislike[0][0] 

            result[name] = [name_user, article, link_article, topic, likes, dislikes, views]
            names.append(name)

        return render_template("home_article.html", records = records,result = result,
         names = names, topic= topic_filter)


if __name__ == '__main__':
    app.run(debug = True)
