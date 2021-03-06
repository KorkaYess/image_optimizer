from flask import Flask, request, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from get_key import api
import logging
import tinify
import io
import subprocess


app = Flask(__name__)
app.secret_key = 'secret key'
app.logger.setLevel(logging.DEBUG)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://postgres:password@localhost:5432/api'
db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


class api_keys(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True)
    counter = db.Column(db.Integer, unique=False)

    def __init__(self, key, counter):
        self.key = key
        self.counter = counter
# db.create_all()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            return file


def post_tinyjpg(source, db):
    try:
        get_key = api_keys.query.filter(api_keys.counter < 500).first()
        tinify.key = get_key.key
    except Exception:
        new_api_key(db)
        get_key = api_keys.query.filter(api_keys.counter == 0).first()
        tinify.key = get_key.key
    source_data = source.read()
    result_data = tinify.from_buffer(source_data).to_buffer()
    get_key.counter = get_key.counter + 1
    db.session.commit()
    response = io.BytesIO(result_data)
    response.filename = source.filename
    return response


def new_api_key(db):
    key = api()
    new_key = api_keys(key=key, counter=0)
    db.session.add(new_key)
    db.session.commit()
    return key


@app.route('/upload', methods=['POST', 'GET'])
def root():
    if 'file' not in request.files:
        return Response('No file part',
                        status=422,
                        mimetype='application /json')
    else:
        try:
            img = upload_file()
            img_small = post_tinyjpg(img, db)
            subprocess.Popen(
                'killall chromedriver', shell=True
            )
            subprocess.Popen(
                'killall chrome', shell=True
            )
            return send_file(img_small, attachment_filename=img_small.filename)
        except Exception as e:
            logging.error(e, exc_info=True)
            return Response('Picture format is not correct',
                            status=422,
                            mimetype='application /json')


if __name__ == '__main__':
    app.run(debug=True)
