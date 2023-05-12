from app import db
from typing import List, Generator
from datetime import datetime
from sqlalchemy import or_
import os

_upload_folder = os.environ.get("UPLOAD_FOLDER")


class File(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    date_posted: datetime = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    last_downloaded: datetime = db.Column(db.DateTime, nullable=True, default=None)
    user_id: int = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True, default=None
    )
    file_name: str = db.Column(db.String(100), nullable=True, default=None)
    file_size: str = db.Column(db.String, nullable=True, default=None)
    file_type: str = db.Column(db.String(100), nullable=True, default=None)
    deleted: bool = db.Column(db.Boolean, nullable=False, default=False)
    date_deleted: datetime = db.Column(db.DateTime, nullable=True, default=None)
    private: bool = db.Column(db.Boolean, nullable=False, default=False)
    details: str = db.Column(db.String(200), nullable=True, default=None)

    def __init__(
        self,
        file_name: str,
        user_id: int = None,
        date_posted: datetime = datetime.utcnow(),
        private: bool = False,
        details=None,
    ) -> None:
        self.file_name = file_name
        self.user_id = user_id
        self.date_posted = date_posted
        self.private = private
        self.details = details

    def __repr__(self) -> str:
        return f"File('{self.file_name}', '{self.date_posted}')"

    def is_owned_by_user(self, user_id: int) -> bool:
        return self.user_id == user_id

    def is_anonymous(self) -> bool:
        return self.user_id is None

    def is_private(self) -> bool:
        return self.private

    def save(self) -> int:
        db.session.add(self)
        db.session.commit()

    def delete(self):
        try:
            os.remove(os.path.join(_upload_folder, self.file_name))
        except FileNotFoundError:
            raise Exception("File not found")
        self.deleted = True
        db.session.commit()

    def is_editable(self, user_id: int) -> bool:
        if user_id is None:
            return False
        from app.models.user import User
        return (
            self.is_owned_by_user(user_id)
            or User.query.filter_by(id=user_id).first().is_admin()
        )

    def can_be_viewed(self, user_id) -> bool:
        if user_id is None:
            return not self.private or self.is_anonymous()
        return self.is_owned_by_user(user_id) or not self.private

    def get_owner(self):
        from app.models.user import User

        owner = User.query.filter_by(id=self.user_id).first()
        return owner

    @staticmethod
    def get_all_user_files(user_id):
        return [
            file
            for file in File.query.filter_by(user_id=user_id).all()
            if not file.deleted
        ]

    @staticmethod
    def return_index_page_files(user_id):
        File.read_info_from_uploads_dir()
        return [
            file
            for file in File.query.all()
            if file.can_be_viewed(user_id) and not file.deleted
        ]

    @staticmethod
    def read_info_from_uploads_dir() -> None:
        for file in File.scan_folder():
            file_data = File.query.filter_by(file_name=file).first()
            if file_data is not None:
                if file_data.file_size is None:
                    file_size_bytes = os.path.getsize(
                        os.path.join(_upload_folder, file)
                    )
                    file_size_kb = file_size_bytes / 1024
                    file_size_mb = file_size_kb / 1024
                    file_size_gb = file_size_mb / 1024

                    if file_size_bytes < 1024:
                        file_data.file_size = f"{file_size_bytes} B"
                    elif file_size_kb < 1024:
                        file_data.file_size = f"{file_size_kb:.2f} KB"
                    elif file_size_mb < 1024:
                        file_data.file_size = f"{file_size_mb:.2f} MB"
                    else:
                        file_data.file_size = f"{file_size_gb:.2f} GB"

                if file_data.file_type is None:
                    file_data.file_type = file.split(".")[-1]
                db.session.commit()

    @staticmethod
    def scan_folder() -> Generator[str, None, None]:
        for file in os.listdir(_upload_folder):
            yield file

    @staticmethod
    def get_admin_files(current_user):
        if current_user.is_admin():
            return File.query.all()

    @staticmethod
    def search(search_term: str, user_id) -> List:
        if search_term != "":
            return [
                file
                for file in File.query.filter(
                    or_(
                        File.file_name.contains(search_term),
                        File.details.contains(search_term),
                    )
                )
                if file.can_be_viewed(user_id) and not file.deleted
            ]
        return []

    @classmethod
    def init_with_id(cls, filename: str):
        file = File(file_name=filename)
        file.save()
        db.session.refresh(file)
        return file
