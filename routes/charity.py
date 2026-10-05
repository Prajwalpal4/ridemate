from flask import Blueprint, render_template

charity = Blueprint("charity", __name__)


@charity.route("/charity")
def charity_payment():

    return render_template("charity.html")