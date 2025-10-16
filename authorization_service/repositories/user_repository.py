from typing import Optional

from sqlalchemy.orm import Session

from authorization_service.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # Basic queries
    def get(self, id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    # Mutations
    def create_user(self, *, email: str, full_name: Optional[str], hashed_password: str) -> User:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
