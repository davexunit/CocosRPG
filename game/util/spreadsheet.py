'''This module loads Open Document Format spreadsheets into easy to use
dictionaries.
'''

from lpod.document import odf_get_document

def load_spreadsheet(filename):
    '''Loads all of the sheets in a .ods spreadsheet file. Returns a dictionary
    of sheet names mapped to row lists.
    '''
    # Store all sheets here
    sheets = {}

    # Open document and get content body
    document = odf_get_document(filename)
    body = document.get_content().get_body()

    # Load all sheets
    for table in body.get_table_list():
        sheets[table.get_name()] = load_table(table)

    return sheets

def load_table(table):
    # Get table rows
    rows = table.get_row_list()
    # Header
    header_row = rows[0][1]
    # Remove header from rows
    rows = rows[1:len(rows)]

    # Read header
    header = []
    for j, column in header_row.get_cell_list():
        header.append(column.get_value())

    # Read rows
    table_rows = []
    for i, row in rows:
        row_dict = {}
        for j, column in row.get_cell_list():
            row_dict[header[j]] = column.get_value()
        table_rows.append(row_dict)

    return table_rows

if __name__ == '__main__':
    sheets = load_spreadsheet('data.ods')

    table = sheets['People']

    for row in table:
        print row['name'], row['type']
