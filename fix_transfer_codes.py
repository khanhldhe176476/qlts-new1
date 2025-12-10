from app import app
from models import db, AssetTransfer


def main():
    with app.app_context():
        transfers = AssetTransfer.query.order_by(AssetTransfer.id.asc()).all()
        updated = 0
        for t in transfers:
            new_code = f"BG{t.id}"
            if t.transfer_code != new_code:
                t.transfer_code = new_code
                updated += 1
        if updated:
            db.session.commit()
        print(f"Updated {updated} transfer codes.")


if __name__ == "__main__":
    main()


