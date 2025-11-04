import pandas as pd
import argparse
import logging
import sys
from pathlib import Path

# -------------------------------
# Setup logging
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# -------------------------------
# Helper functions
# -------------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize the dataframe."""
    logging.info("Starting data cleaning...")

    # Handle missing values
    df = df.fillna("N/A")

    # Try parsing any columns that look like dates
    for col in df.columns:
        if "date" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception as e:
                logging.warning(f"Could not parse dates in column '{col}': {e}")

    # Normalize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    logging.info("Data cleaning complete.")
    return df


def convert_csv_to_xlsx(input_file: Path, output_path: Path):
    """Read CSV, clean data, and export to Excel."""
    if not input_file.exists():
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)

    try:
        logging.info(f"Reading CSV file: {input_file}")
        df = pd.read_csv(input_file)

        logging.info("Cleaning data...")
        df = clean_data(df)

        output_path = output_path / f"{input_file.stem}_cleaned.xlsx"
        logging.info(f"Exporting to Excel: {output_path}")

        df.to_excel(output_path, index=False, engine='openpyxl')

        logging.info("File successfully saved.")
    except Exception as e:
        logging.error(f"Failed to process file: {e}")
        sys.exit(1)


# -------------------------------
# CLI
# -------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Convert and clean CSV data, then export to XLSX."
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Path to input CSV file"
    )
    parser.add_argument(
        "--output", "-o", required=False, default=".", help="Output directory path"
    )

    args = parser.parse_args()

    input_file = Path(args.input)
    output_path = Path(args.output)

    convert_csv_to_xlsx(input_file, output_path)


if __name__ == "__main__":
    main()
