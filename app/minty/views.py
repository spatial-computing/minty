from flask import jsonify, request, url_for, redirect, current_app, render_template, flash, make_response
from flask.views import MethodView

# from .. import app

class LayerJson(MethodView):
    def get(self):
        return render_template('food/profile.html')
