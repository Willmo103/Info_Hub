from flask import render_template
from flask_login import current_user
from app.models import Note, File
from . import endpoint


@endpoint.route("/")
@endpoint.route("/index")
def index_page():
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = None
    notes = Note.index_page_notes(user_id)
    files = File.return_index_page_files(user_id)
    return render_template(
        "index.html",
        notes=notes,
        files=files,
        user_id=user_id,
        user=current_user,
        title="Info_Hub",
    )
