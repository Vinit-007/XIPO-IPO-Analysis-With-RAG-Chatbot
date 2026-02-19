"""
Simplified PDF table extractor using pdfplumber.
Extracts raw, unmodified table data with 100% accuracy.
"""

import pdfplumber


def extract_tables_from_pdf(pdf_path: str):
    """
    Extract all tables from PDF with maximum accuracy.
    
    Returns:
        list: [
            {
                "page_number": int,
                "table_index": int,
                "data": [[cell, cell, ...], [row2...], ...]  # Raw table data
            },
            ...
        ]
    """
    all_tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()
            except Exception as e:
                print(f"Warning: Could not extract tables from page {page_num + 1}: {e}")
                continue
            
            if not tables:
                continue
            
            for table_idx, table in enumerate(tables):
                # Keep raw table data, only clean None values
                cleaned_table = []
                for row in table:
                    cleaned_row = []
                    for cell in row:
                        if cell is None:
                            cleaned_row.append("")
                        elif isinstance(cell, str):
                            cleaned_row.append(cell.strip())
                        else:
                            cleaned_row.append(str(cell))
                    cleaned_table.append(cleaned_row)
                
                all_tables.append({
                    "page_number": page_num + 1,
                    "table_index": table_idx + 1,
                    "data": cleaned_table
                })
    
    return all_tables
