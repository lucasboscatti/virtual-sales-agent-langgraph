import logging
import os
import zipfile
from contextlib import closing

import pandas as pd
import requests
from utils.database_functions import get_connection, insert_product

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_and_extract_db(url: str, download_path: str, db_path: str) -> bool:
    """
    Downloads and extracts the SQLite database.

    Arguments:
        url (str): The URL of the database file.
        download_path (str): The path to save the downloaded file.
        db_path (str): The path to save the extracted database file.

    Returns:
        bool: True if the database was downloaded and extracted successfully, False otherwise.
    """
    try:

        logger.info(f"Downloading database from {url}...")
        response = requests.get(url)
        response.raise_for_status()

        with open(download_path, "wb") as file:
            file.write(response.content)
        logger.info(f"Database downloaded successfully to {download_path}")

        if zipfile.is_zipfile(download_path):
            logger.info(f"Extracting database from {download_path}...")
            with zipfile.ZipFile(download_path, "r") as zip_ref:
                zip_ref.extractall(os.path.dirname(db_path))
                os.remove(download_path)
            logger.info(f"Database extracted successfully to {db_path}")
        else:
            logger.warning(
                f"{download_path} is not a zip file. Assuming it is the database file."
            )
            os.rename(download_path, db_path)

        return True
    except Exception as e:
        logger.error(f"Failed to download or extract database: {e}")
        return False


def execute_sql_file(file_path: str) -> bool:
    """
    Executes SQL commands from a file.

    Arguments:
        file_path (str): The path to the SQL file.

    Returns:
        bool: True if the SQL commands were executed successfully, False otherwise.
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


def insert_products_from_json(file_path: str) -> bool:
    """
    Inserts products into the database from a JSON file.

    Arguments:
        file_path (str): The path to the JSON file containing product data.

    Returns:
        bool: True if the products were inserted successfully, False otherwise.
    """
    try:
        df = pd.read_json(file_path)
    except ValueError as e:
        logger.error(f"Failed to load JSON file: {e}")
        return

    for _, row in df.iterrows():
        try:
            insert_product(
                product_name=row.get("product_name").lower(),
                category=row.get("category").lower(),
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
    db_url = "https://www.sqlitetutorial.net/wp-content/uploads/2018/03/chinook.zip"
    download_path = "database/db/chinook.zip"
    db_path = "database/db/chinook.db"

    # Download and extract the database
    if not download_and_extract_db(db_url, download_path, db_path):
        return

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
