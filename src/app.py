"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, Character, Gender, Specie


#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


#CRUD

@app.route('/characters', methods=["GET"])
def get_characters():
    characters = Character.query.all()
    serialized_characters = [character.serialize() for character in characters]
    return jsonify({"characters": serialized_characters})

@app.route("/character", methods=["POST"])
def create_character():
    body = request.json

    name = body.get("name", None)
    gender = body.get("gender", None)
    specie = body.get("specie", None)
    dimension = body.get("dimension", None)

    if name is None or gender is None or specie is None or dimension is None:
        return jsonify({"error": "missing fields"}), 400

    character = Character(name=name, gender=Gender(gender), specie=Specie(specie), dimension=dimension)

    try:
        db.session.add(character)
        db.session.commit()
        db.session.refresh(character)

        return jsonify({"message": f"Character created {character.name}!"}), 201

    except Exception as error:
        return jsonify({"error": f"{error}"}), 500


@app.route("/character/<int:id>", methods=["GET"])
def get_character_by_id(id):
    try:
        character = Character.query.get(id)
        if character is None:
            return jsonify({'error': "Character not found!"}), 404
        return jsonify({"character": character.serialize()}), 200

    except Exception as error:
        return jsonify({"error": f"{error}"}), 500



# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
