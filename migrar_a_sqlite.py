# -*- coding: utf-8 -*-
"""Migra los datos de telezarcomunicaciones (MySQL 172.28.3.38) a SQLite.

Uso:
    python migrar_a_sqlite.py

Genera: instance/telezarcomunicaciones.db
"""
import os
import sys

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance"), exist_ok=True)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

MYSQL_URL = (
    "mysql+pymysql://root:Matthias1987*@172.28.3.38:3306/"
    "telezarcomunicaciones?charset=utf8mb4"
)
SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "telezarcomunicaciones.db")
SQLITE_URL = "sqlite:///" + SQLITE_PATH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import (  # noqa: E402
    Brand,
    Category,
    Certificate,
    ContactMessage,
    GalleryImage,
    Page,
    Product,
    Service,
    Setting,
    User,
)

MODELOS = [
    User, Setting, Page, Service, Category, Product,
    Brand, Certificate, ContactMessage, GalleryImage,
]


def main():
    origen = create_engine(MYSQL_URL)
    destino = create_engine(SQLITE_URL)

    # Crea todas las tablas en SQLite
    from app.extensions import db
    from sqlalchemy.orm import DeclarativeBase  # noqa: F401
    # Creamos las tablas usando metadata directamente
    db.metadata.create_all(destino)

    SesionOrigen = sessionmaker(bind=origen)
    SesionDestino = sessionmaker(bind=destino)
    so = SesionOrigen()
    sd = SesionDestino()

    total = 0
    for Modelo in MODELOS:
        filas = so.query(Modelo).all()
        for fila in filas:
            datos = {
                c.name: getattr(fila, c.name)
                for c in Modelo.__table__.columns
            }
            sd.merge(Modelo(**datos))
        sd.commit()
        print(f"* {Modelo.__tablename__}: {len(filas)} filas")
        total += len(filas)

    so.close()
    sd.close()
    print(f"\nListo. {total} filas migradas a: {SQLITE_PATH}")


if __name__ == "__main__":
    main()