from datetime import datetime
from app import db


class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True,
        default=None,
    )
    file_id = db.Column(
        db.Integer, db.ForeignKey("file.id", ondelete="NO ACTION"), nullable=False
    )

    def __repr__(self) -> str:
        return f"Upload('{self.upload_date}', '{self.user_id}', '{self.file_id}')"

    def __init__(
        self,
        file_id: int,
        user_id=None,
    ) -> None:
        self.user_id = user_id
        self.file_id = file_id

    def save(self) -> int:
        db.session.add(self)
        db.session.commit()
        return True

    @staticmethod
    def record_upload(user_id: int, file_id: int) -> None:
        ul: Upload = Upload(user_id, file_id)
        db.session.add(ul)
        db.session.commit()
