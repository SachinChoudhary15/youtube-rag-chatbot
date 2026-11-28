



from sqlalchemy.orm import Session

from app.db.models import User

def create_user(db: Session, user_data: dict) -> User:
    try:
        new_user = User(**user_data)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except Exception:
        db.rollback()
        raise

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()

    return (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )