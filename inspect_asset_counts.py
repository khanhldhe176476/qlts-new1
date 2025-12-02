from app import app
from models import db, Asset


def show_counts():
    with app.app_context():
        counts = db.session.query(
            Asset.user_id,
            db.func.count(Asset.id)
        ).filter(
            Asset.deleted_at.is_(None),
            Asset.user_id.isnot(None)
        ).group_by(Asset.user_id).all()
        print("entries", len(counts))
        print(counts[:10])


if __name__ == "__main__":
    show_counts()


