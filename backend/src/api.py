import os
import sys

from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

RECIPE_KEYS = ["name", "color", "parts"]

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''


# db_drop_and_create_all()


@app.route("/drinks")
def get_all_drinks():
    try:
        drinks_query = Drink.query.order_by(Drink.id).all()
        drinks = []
        for drink in drinks_query:
            drinks.append(drink.short())

        return jsonify({
            "success": True,
            "drinks": drinks
        }), 200

    except:
        abort(500)


@app.route("/drinks-detail")
@requires_auth("get:drink-details")
def get_all_drinks_detail(payload):
    try:
        drinks_query = Drink.query.order_by(Drink.id).all()
        drinks = []
        for drink in drinks_query:
            drinks.append(drink.long())

        return jsonify({
            "success": True,
            "drinks": drinks
        }), 200

    except:
        abort(500)


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def add_drink(payload):
    try:
        request_body = request.get_json()
        if "title" not in request_body or "recipe" not in request_body:
            raise TypeError

        if request_body["title"] == "" or len(request_body["recipe"]) == 0:
            raise ValueError

        for recipe in request_body["recipe"]:
            if not all(key in recipe for key in RECIPE_KEYS):
                raise KeyError

            if recipe["name"] == "" or recipe["color"] == "" or recipe["parts"] == 0:
                raise ValueError

        drink_title = request_body["title"]
        drink_recipe = json.dumps(request_body["recipe"])
        new_drink = Drink(title=drink_title, recipe=drink_recipe)
        new_drink.insert()

        return jsonify({
            "success": True,
            "drinks": [new_drink.long()]
        }), 200

    except (TypeError, KeyError, ValueError):
        abort(422)

    except:
        abort(500)


@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink_details(payload, drink_id):
    drink = Drink.query.get_or_404(drink_id)

    try:
        request_body = request.get_json()
        if not bool(request_body):
            raise TypeError

        if "title" in request_body:
            if request_body["title"] == "":
                raise ValueError

            drink.title = request_body["title"]

        if 'recipe' in request_body:
            if len(request_body["recipe"]) == 0:
                raise ValueError

            for recipe in request_body["recipe"]:
                if not all(key in recipe for key in RECIPE_KEYS):
                    raise KeyError

                if recipe["name"] == "" or recipe["color"] == "" or recipe["parts"] == 0:
                    raise ValueError

            drink.recipe = json.dumps(request_body["recipe"])

        drink.update()

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        }), 200

    except (TypeError, ValueError, KeyError):
        abort(422)

    except:
        abort(500)


@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(payload, drink_id):
    drink = Drink.query.get_or_404(drink_id)

    try:
        drink.delete()

        return jsonify({
            "success": True,
            "delete": drink.id
        }), 200

    except:
        abort(500)


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(422)
@app.errorhandler(500)
def error_handler(error):
    return jsonify({
        'success': False,
        'error': error.code,
        'message': error.description
    }), error.code
