import csv


def csv_to_html(csv_file_path, html_file_path, page_title="CSV Viewer"):
    # Read the CSV file
    with open(csv_file_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        rows = list(reader)

    # Create the HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page_title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f4f4f4;
            }}
        </style>
    </head>
    <body>
        <h1>{page_title}</h1>
        <table>
    """

    # Add the rows from the CSV
    if rows:
        # Add header row
        html_content += "<thead><tr>"
        for header in rows[0]:
            html_content += f"<th>{header}</th>"
        html_content += "</tr></thead><tbody>"

        # Add data rows
        for row in rows[1:]:
            html_content += "<tr>"
            for cell in row:
                html_content += f"<td>{cell}</td>"
            html_content += "</tr>"
        html_content += "</tbody>"
    else:
        html_content += "<tr><td colspan='100%'>No data found</td></tr>"

    # Close table and HTML
    html_content += """
        </table>
    </body>
    </html>
    """

    # Write to the HTML file
    with open(html_file_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

    print(f"HTML file created at: {html_file_path}")


# Example usage
csv_to_html(
    "all_nodups.csv", "options122024.html", page_title="Option Date for 12-2024"
)
csv_to_html("NIFTY_data.csv", "nifty.html", page_title="NIFTY50 Data")
