from flask import Blueprint

from . import repository
from .db import get_db

bp = Blueprint("data_read", __name__)


@bp.route("/all_data", methods=["GET"])
def get_all_data():
    db = get_db()
    return {"data": [dict(x) for x in db.execute("SELECT * FROM flights").fetchall()]}


@bp.route("/recent_data", methods=["GET"])
def get_recent_data():
    db = get_db()
    return {"data": [dict(x) for x in repository.get_recent(db, minutes=1)]}
