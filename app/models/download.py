from datetime import datetime
from app import db


class Download(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    download_date: datetime = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    file_id = db.Column(
        db.Integer, db.ForeignKey("file.id", ondelete="NO ACTION"), nullable=False
    )

    def __init__(
        self,
        file_id: int,
        user_id=None,
        download_date: datetime = datetime.utcnow(),
    ) -> None:
        self.user_id = user_id
        self.file_id = file_id
        self.download_date = download_date

    def __repr__(self) -> str:
        return f"Download('{self.download_date}', '{self.user_id}', '{self.file_id}')"

    def save(self) -> None:
        db.session.add(self)
        db.session.commit()

    @classmethod
    def record_download(cls, file_id, user_id=None):
        download = cls(
            file_id=file_id,
            user_id=user_id,
            download_date=datetime.utcnow(),
        )
        db.session.add(download)
        db.session.commit()
