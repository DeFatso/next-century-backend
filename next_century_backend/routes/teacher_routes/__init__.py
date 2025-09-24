from flask import Blueprint

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

# Import individual route files so they register routes with teacher_bp
from . import auth
from . import lessons
from . import grading
