import os
import uuid
import sqlalchemy

from datetime import datetime
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = 'sqlite:///{}'.format(os.path.join(project_dir, 'onetimeshare.db'))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

secret_key = '12345'

db = SQLAlchemy(app)

class Secret(db.Model):
    secret = db.Column(StringEncryptedType(sqlalchemy.Unicode, secret_key, AesEngine, 'pkcs5'), nullable=False)
    sid = db.Column(db.String(32), unique=True, nullable=False, primary_key=True)
    expiration = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
        return '<Secret: {}>'.format(self.secret)

@app.route('/', methods=['GET', 'POST'])
def add_secret():
    sid = ''
    url = ''
    exp = ''
    if request.form:
        exp = datetime.strptime(str(request.form.get('expiration')), '%Y-%m-%dT%H:%M')
        sid = str(uuid.uuid4()).replace('-','')
        secret = Secret(secret=request.form.get('secret'), expiration=exp, sid=sid)
        db.session.add(secret)
        db.session.commit()
        url = request.base_url
    
    return render_template('index.html', sid=sid, url=url)
  
@app.route('/<sid>', methods=['GET'])
def get_secret(sid):
    secret = Secret.query.filter_by(sid=sid).first()
    if secret is not None:
        db.session.delete(secret)
        db.session.commit()
        if secret.expiration > datetime.now():
            return render_template('get.html', secret=secret)

    return render_template('get.html', secret=Secret(secret='Nothing to see here. Move along'))  

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
