from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    send_from_directory,
    Response,
)
from flask_login import current_user, login_required
from app.models import File, Upload, Download, User, Deletion
from app.forms import DeleteFileForm, FileUploadForm, EditFileForm
from werkzeug.utils import secure_filename as s_fn
import os
from . import endpoint

_upload_folder: str = os.environ.get("UPLOAD_FOLDER")


@endpoint.route("/file/upload", methods=["POST"])
def upload_file():
    # check which field the file was uploaded to
    form = FileUploadForm()
    if form.file.data is None:
        uploaded_file = form.file_dz.data
    elif form.file_dz.data is None:
        uploaded_file = form.file.data
    else:
        flash("Failed to upload file")
        return redirect(url_for("routes.index_page"))
    # get secure filename and create file object with s new id
    secure_filename = s_fn(uploaded_file.filename)
    file = File.init_with_id(secure_filename)
    # update file object with form data
    if current_user.is_authenticated:
        if file:
            file.user_id = current_user.id
            file.private = form.private.data
            file.details = form.details.data
            file.save()
        else:
            raise Exception("Failed to create new file")
        new_upload = Upload(
            file.id,
            current_user.id,
        )
        saved = new_upload.save()
    else:
        # if the user is not logged in, create an anonymous file
        new_upload = Upload(file_id=file.id)
        saved = new_upload.save()
    if saved and file.id is not None:
        # make sure the file has been saved and the upload recorded before saving the file
        uploaded_file.save(os.path.join(_upload_folder, file.file_name))
        flash("File uploaded successfully")
        return redirect(url_for("routes.index_page"))

    flash("File upload failed")
    return redirect(url_for("routes.index_page"))


@endpoint.route("/user/files")
@login_required
def get_user_files() -> Response:
    files = File.get_all_user_files(current_user.id)
    return render_template(
        "file_search_results.html", files=files, user=current_user, my_files=True
    )


@endpoint.route("/file/<int:file_id>/edit", methods=["GET", "POST"])
@login_required
def edit_file(file_id) -> Response:
    file = File.query.get_or_404(file_id)
    form = EditFileForm()
    if request.method == "GET":
        return render_template(
            "file.html", title="Edit File", form=form, user=current_user, file=file
        )
    elif request.method == "POST":
        if current_user.is_admin() or file.is_owned_by_user(current_user.id):
            file.file_name = form.file_name.data
            file.private = form.private.data
            file.details = form.details.data
            file.save()
            flash("Your file has been updated.")
            return redirect(url_for("routes.index_page"))
        else:
            flash("You do not have permission to edit this file.")
            return redirect(url_for("routes.index_page"))


@endpoint.route("/file/<int:file_id>/delete", methods=["GET", "POST"])
@login_required
def delete_file(file_id) -> Response:
    file: File = File.query.get_or_404(file_id)
    form = DeleteFileForm()
    user = User.query.get_or_404(current_user.id)
    if user.is_admin():
        if request.method == "GET":
            return render_template(
                "delete_file.html",
                title="Delete File",
                form=form,
                file=file,
            )
        if form.validate_on_submit():
            file.delete()
            Deletion(file_id, current_user.id).save()
        flash("Your file has been deleted.")
        return redirect(url_for("routes.index_page"))
    else:
        flash("You do not have permission to delete this file.")
    return redirect(url_for("routes.index_page"))


from flask import Response, make_response


@endpoint.route("/file/<int:file_id>/download")
def download_file(file_id) -> Response:
    file = File.query.get_or_404(file_id)
    if current_user.is_authenticated:
        if not file.is_private() or file.is_owned_by_user(current_user.id):
            Download.record_download(file_id, current_user.id)
            # setting the content headers so that the browser knows to download the file
            response = make_response(
                send_from_directory(_upload_folder, file.file_name, as_attachment=True)
            )
            response.headers[
                "Content-Disposition"
            ] = f"attachment; filename={file.file_name}"
            response.headers["Content-Type"] = "application/octet-stream"
            return response
    elif not file.is_private() or file.is_anonymous():
        Download.record_download(file_id)
        # setting the content headers so that the browser knows to download the file
        response = make_response(
            send_from_directory(_upload_folder, file.file_name, as_attachment=True)
        )
        response.headers[
            "Content-Disposition"
        ] = f"attachment; filename={file.file_name}"
        response.headers["Content-Type"] = "application/octet-stream"
        return response
    else:
        flash("You do not have permission to download this file.")
        return redirect(url_for("routes.login"))


@endpoint.route("/file/search", methods=["GET", "POST"])
def search_files() -> Response:
    if request.method == "POST":
        search_term = request.form["search_term"]
        try:
            id = current_user.id
        except AttributeError:
            id = None
        files = File.search(search_term, id)
        if len(files) == 0:
            files = None
        return render_template(
            "file_search_results.html",
            search_term=search_term,
            title="Search Results",
            files=files,
        )
    return render_template(url_for("routes.index_page"))
