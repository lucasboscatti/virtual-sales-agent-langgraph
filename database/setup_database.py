import logging
import os
from contextlib import closing

import pandas as pd
import requests
from utils.database_functions import get_connection, insert_product

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def execute_sql_file(file_path: str) -> bool:
    """
    Executes SQL commands from a file.

    :param file_path: The path to the SQL file containing the commands.
    :return: True if the SQL script executed successfully, False otherwise.
    """
    try:
        with open(file_path, "r") as file:
            sql_script = file.read()

    except FileNotFoundError:
        logger.error(f"SQL file not found: {file_path}")
        return False

    try:
        with get_connection() as conn:
            with closing(conn.cursor()) as cursor:
                cursor.executescript(sql_script)
                conn.commit()
        logger.info(f"SQL script executed successfully from {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error executing SQL script from {file_path}: {e}")
        return False


def insert_products_from_json(file_path: str) -> None:
    """
    Inserts products into the database from a JSON file.

    :param file_path: The path to the JSON file containing product data.
    :return: None
    """
    try:
        df = pd.read_json(file_path)
    except ValueError as e:
        logger.error(f"Failed to load JSON file: {e}")
        return

    for _, row in df.iterrows():
        try:
            insert_product(
                product_name=row.get("product_name"),
                category=row.get("category"),
                description=row.get("description"),
                price=row.get("price"),
                quantity=row.get("quantity"),
            )
        except Exception as e:
            logger.error(f"Failed to insert product: {row}. Error: {e}")

    logger.info("Products inserted successfully.")
    return True


def main():
    """
    Main function to download the database, execute SQL scripts, and insert products.
    """
    logger.info("Starting database setup...")
    sqlite_file = "database/db/schemas.sql"
    products_file = "database/db/products.json"

    # Execute SQL schema file
    if not execute_sql_file(sqlite_file):
        return

    # Insert products from JSON file
    if not insert_products_from_json(products_file):
        return

    logger.info("Database setup completed successfully.")


if __name__ == "__main__":
    main()
