from flask import jsonify, request, url_for, redirect, current_app, render_template, flash, make_response
from flask.views import MethodView

class VizType(MethodView):
	def __init__(self):
		pass
