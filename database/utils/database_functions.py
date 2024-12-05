import logging
import sqlite3
from contextlib import closing

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_connection(db_path):
    """
    Establish a connection to the SQLite database.
    :return: SQLite connection object.
    """
    return sqlite3.connect(db_path)


def insert_product(product_name, category, description, price, quantity, db_path):
    """
    Inserts a new product into the Products table.
    """
    query = """
    INSERT INTO Products (ProductName, Category, Description, Price, Quantity)
    VALUES (?, ?, ?, ?, ?);
    """
    with get_connection(db_path) as conn:
        with closing(conn.cursor()) as cursor:
            try:
                cursor.execute(
                    query, (product_name, category, description, price, quantity)
                )
                conn.commit()
                logging.info("Product inserted successfully.")
            except sqlite3.Error as e:
                logging.error(f"Error inserting product: {e}")