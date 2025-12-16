from flaskapp.db import get_db
from flask import redirect, url_for, Blueprint, request
import datetime



bp = Blueprint("data_read", __name__)


@bp.route("/all_data", methods=["GET"])
def get_all_data():
    db= get_db()
    
    return db.execute("SELECT * FROM flights").fetchall()