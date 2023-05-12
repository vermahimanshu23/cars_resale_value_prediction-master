'''
This is the main file for the application. 
It contains the routes and views for the application.
'''

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import opendb, DB_URL
from database import User, Profile, Product
from db_helper import *
from validators import *
from logger import log
from werkzeug.utils import secure_filename
import os
import joblib   
import pandas as pd
import numpy as np

app = Flask(__name__)
app.secret_key  = '()*(#@!@#)'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

import math
def session_add(key, value):
    session[key] = value

def save_file(file):
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    return path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    if not validate_email(email):
        flash('Invalid email', 'danger')
        return redirect(url_for('index'))
    if not validate_password(password):
        flash('Invalid password', 'danger')
        return redirect(url_for('index'))
    db = opendb()
    user = db.query(User).filter_by(email=email).first()
    if user is not None and user.verify_password(password):
        session_add('user_id', user.id)
        session_add('user_name', user.name)
        session_add('user_email', user.email)
        session_add('isauth', True)
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email or password', 'danger')
        return redirect(url_for('index'))
    
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    cpassword = request.form.get('cpassword')
    db = opendb()
    if not validate_username(name):
        flash('Invalid username', 'danger')
        return redirect(url_for('index'))
    if not validate_email(email):
        flash('Invalid email', 'danger')
        return redirect(url_for('index'))
    if not validate_password(password):
        flash('Invalid password', 'danger')
        return redirect(url_for('index'))
    if password != cpassword:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('index'))
    if db.query(User).filter_by(email=email).first() is not None    :
        flash('Email already exists', 'danger')
        return redirect(url_for('index'))
    elif db.query(User).filter_by(name=name).first() is not None:
        flash('Username already exists', 'danger')
        return redirect(url_for('index'))
    else:
        db_save(User(name=name, email=email, password=password))
        flash('User registered successfully', 'success')
        return redirect(url_for('index'))
    
@app.route('/dashboard')
def dashboard():
    if session.get('isauth'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('index'))

@app.route('/profile/add', methods=['POST'])
def add_profile():
    if session.get('isauth'):
        user_id = session.get('user_id')
        city = request.form.get('city')
        gender = request.form.get('gender')
        avatar = request.files.get('avatar')
        db = opendb()
        if not validate_city(city):
            flash('Invalid city', 'danger')
            return redirect(url_for('dashboard'))
        if not validate_avatar(avatar):
            flash('Invalid avatar file', 'danger')
            return redirect(url_for('dashboard'))
        if db.query(Profile).filter_by(user_id=user_id).first() is not None:
            flash('Profile already exists', 'danger')
            return redirect(url_for('view_profile'))
        else:
            db_save(Profile(user_id = user_id, city=city, gender=gender, avatar=save_file(avatar)))
            flash('Profile added successfully', 'success')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))
        
@app.route('/profile/edit', methods=['POST'])
def edit_profile():
    if session.get('isauth'):
        profile = db_get_by_field(Profile, user_id=session.get('user_id'))
        if profile is not None:
            profile.city = request.form.get('city')
            profile.gender = request.form.get('gender')
            avatar = request.files.get('avatar')
            if avatar is not None:
                profile.avatar = save_file(avatar)
            db_save(profile)
            flash('Profile updated successfully', 'success')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))    

@app.route('/profile')
def view_profile():
    if session.get('isauth'):
        profile = db_get_by_field(Profile, user_id=session.get('user_id'))
        if profile is not None:
            return render_template('profile.html', profile=profile)
        else:
            flash(f'<a class="text-danger" href="#" data-bs-toggle="modal" data-bs-target="#profileModal">Create a profile</a>', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))

@app.route('/form/audi', methods=['GET','POST'])
def form_audi():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('audi/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['audi_price'] = math.ceil(result)
        return redirect('/form/audi')
    return render_template('audi_form.html')

@app.route('/form/bmw', methods=['GET','POST'])
def form_bmw():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('bmw/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['bmw_price'] = math.ceil(result)
        return redirect('/form/bmw')
    return render_template('bmw_form.html')

@app.route('/form/focus', methods=['GET','POST'])
def form_focus():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('focus/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['focus_price'] = math.ceil(result)
        return redirect('/form/focus')
    return render_template('focus_form.html')

@app.route('/form/ford', methods=['GET','POST'])
def form_ford():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('ford/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['ford_price'] = math.ceil(result)
        return redirect('/form/ford')
    return render_template('ford_form.html')

@app.route('/form/skoda', methods=['GET','POST'])
def form_skoda():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('skoda/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['skoda_price'] = math.ceil(result)
        return redirect('/form/skoda')
    return render_template('skoda_form.html')

@app.route('/form/merc', methods=['GET','POST'])
def form_merc():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('merc/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['merc_price'] = math.ceil(result)
        return redirect('/form/merc')
    return render_template('merc_form.html')

@app.route('/form/toyota', methods=['GET','POST'])
def form_toyota():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('toyota/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['toyota_price'] = math.ceil(result)
        return redirect('/form/toyota')
    return render_template('toyota_form.html')

@app.route('/form/vauxhall', methods=['GET','POST'])
def form_vauxhall():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('vauxhall/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['vauxhall_price'] = math.ceil(result)
        return redirect('/form/vauxhall')
    return render_template('vauxhall_form.html')

@app.route('/form/volkswagen', methods=['GET','POST'])
def form_volkswagen():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('volkswagen/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['volkswagen_price'] = math.ceil(result)
        return redirect('/form/volkswagen')
    return render_template('volkswagen_form.html')

@app.route('/form/hyundi', methods=['GET','POST'])
def form_hyundai():
    if request.method == 'POST':
        transmission = request.form.get('transmission')
        fueltype = request.form.get('fueltype')
        carmodel = request.form.get('carmodel')
        year = request.form.get('year')
        mileage = request.form.get('mileage')
        tax = request.form.get('tax')
        mpg = request.form.get('mpg')
        enginesize = request.form.get('enginesize')
        model = joblib.load('hyundi/rf_model.pkl')
        X = pd.DataFrame({
            "model":[carmodel],
            "year":[year],
            "transmission":[transmission],
            "mileage":[mileage],
            "fuelType":[fueltype],
            "tax":[tax],
            "mpg":[mpg],
            "engineSize":[enginesize]
        })
        print(X.to_dict())
        result = model.predict(X)[0]
        session['hyundi_price'] = math.ceil(result)
        return redirect('/form/hyundi')
    return render_template('hyundi_form.html')

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8000, debug=True)
 