#! -*- coding:utf-8 -*-
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from .forms import LoginForm
from .models import User

#每次requst请求前都运行
@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@app.route('/index')
@login_required
#如果没有登陆，将进入登陆页面
def index():
    user = g.user #用全局量保存用户信息（why not session）
    # user = { 'nickname': 'Miguel' }
    posts = [
        { 
            'author': { 'nickname': 'John' }, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': { 'nickname': 'Susan' }, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template('index.html',
        title = 'Home',
        user = user,
        posts = posts)

#old login
# @app.route('/login', methods = ['GET', 'POST'])
# def login():
#     form = LoginForm()        #生成form实例
#     if form.validate_on_submit():  #如果用户成功提交
#         flash('Login requested for OpenID="' + form.openid.data + '", remember_me=' + str(form.remember_me.data))
#         return redirect('/index')
#     return render_template('login.html',  # 渲染模板
#         title = 'Sign In',
#         form = form,
#         providers = app.config['OPENID_PROVIDERS'])

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler  #告诉openid这是登陆试图
def login():
    #如果已经登陆则跳转
    # if g.user is not None:
    #     print('hello')
    #     print g.user

    if g.user.get_id() is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    print "start"
    form = LoginForm()
    if form.validate_on_submit():
        print 'submit'
        session['remember_me'] = form.remember_me.data  #保存"记住我"
        if form.email.data is None or form.email.data == "":
            flash('Invalid login. Please try again.')
            print 'redirect'
            return redirect(url_for('login'))

        user = User.query.filter_by(email=form.email.data).first()
        print user
        if user is None:
            print 'user is none'
            nickname = form.nickname.data
            if nickname is None or nickname == "":
                nickname = form.email.data.split('@')[0]
            user = User(nickname=nickname, email=form.email.data)
            db.session.add(user)
            db.session.commit()
            print 'add'
        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(user, remember = remember_me)
        print "log in"
        return redirect(request.args.get('next') or url_for('index'))
        # return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])

@lm.user_loader   #登陆回调函数，载入session中的用户
def load_user(id):
    return User.query.get(int(id))

@oid.after_login   #openid登陆后的函数
def after_login(resp):
    print 'after'
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname=nickname, email=resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    print "log in"
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))