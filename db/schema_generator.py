import mysql.connector
import sys
from pathlib import Path

# Add parent directory to path so we can import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import db_config


def generate_schema():

    try:

        print("\nConnecting to database...\n")

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        schema_output = []

        # ====================================
        # FETCH TABLES + COLUMNS
        # ====================================

        schema_query = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME, ORDINAL_POSITION;
        """

        cursor.execute(schema_query, (db_config['database'],))

        schema_results = cursor.fetchall()

        current_table = None

        schema_output.append("========== DATABASE SCHEMA ==========\n")

        for table_name, column_name, data_type in schema_results:

            if table_name != current_table:

                current_table = table_name

                schema_output.append(f"\nTable: {table_name}")
                schema_output.append("-" * 40)

            schema_output.append(
                f"- {column_name} ({data_type})"
            )

        # ====================================
        # FETCH RELATIONSHIPS
        # ====================================

        fk_query = """
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
        AND REFERENCED_TABLE_NAME IS NOT NULL;
        """

        cursor.execute(fk_query, (db_config['database'],))

        fk_results = cursor.fetchall()

        schema_output.append(
            "\n========== RELATIONSHIPS ==========\n"
        )

        for table_name, column_name, ref_table, ref_column in fk_results:

            schema_output.append(
                f"{table_name}.{column_name} "
                f"--> {ref_table}.{ref_column}"
            )

        schema_output.append(
            "\n===================================\n"
        )

        # ====================================
        # WRITE TO FILE
        # ====================================

        output_path = "docs/schema.txt"

        with open(output_path, "w", encoding="utf-8") as file:

            file.write("\n".join(schema_output))

        print(f"Schema successfully written to:")
        print(output_path)

    except mysql.connector.Error as err:

        print(f"Database Error: {err}")

    finally:

        if 'conn' in locals() and conn.is_connected():

            cursor.close()
            conn.close()

            print("\nDatabase connection closed.")


if __name__ == "__main__":
    generate_schema()