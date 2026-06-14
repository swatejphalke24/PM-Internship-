"""Database connection and query helpers"""

import mysql.connector
from flask import current_app, g


def get_db():
    """Get database connection, reusing within request context."""
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB'],
            port=current_app.config.get('MYSQL_PORT', 3306),
            autocommit=False,
            connection_timeout=10,
            use_pure=True
        )
    return g.db


def close_db(e=None):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False, commit=False):
    """Execute a query and return results as dictionaries."""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(sql, args)

        if commit:
            db.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

        rv = cursor.fetchall()

        if one:
            return rv[0] if rv else None

        return rv

    except Exception as e:
        db.rollback()
        raise e

    finally:
        cursor.close()