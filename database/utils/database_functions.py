import logging
import sqlite3
from contextlib import closing

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_connection(db_path: str = "database/db/chinook.db") -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database.

    Arguments:
        db_path (str): The path to the SQLite database file.

    Returns:
        sqlite3.Connection: A connection object to the database.
    """
    return sqlite3.connect(db_path)


def insert_product(
    product_name: str, category: str, description: str, price: float, quantity: int
) -> None:
    """
    Inserts a new product into the Products table.

    Arguments:
        product_name (str): The name of the product.
        category (str): The category of the product.
        description (str): The description of the product.
        price (float): The price of the product.
        quantity (int): The quantity of the product.
    Returns:
        None
    """
    query = """
    INSERT INTO products (ProductName, Category, Description, Price, Quantity)
    VALUES (?, ?, ?, ?, ?);
    """
    with get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            try:
                cursor.execute(
                    query, (product_name, category, description, price, quantity)
                )
                conn.commit()
                logging.info("Product inserted successfully.")
            except sqlite3.Error as e:
                logging.error(f"Error inserting product: {e}")
