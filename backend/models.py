from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username!r})>"


class Car(Base):
    """Car model for storing scraped car listings"""
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    color: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    link: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Car(id={self.id}, brand={self.brand!r}, model={self.model!r}, year={self.year}, price={self.price})>"
