import pandas as pd
import mapper


def validate_csv(csv_file, program, ret=False):
    reader = pd.read_csv(csv_file, iterator=True)

    csv_df = reader.read(0)

    field_mapper = mapper.FieldMapper(program)

    # get csv column names
    cols = csv_df.columns.values

    # check required fields
    if ret:
        return cols, field_mapper.missing_fields(cols)

    mapper.check_missing_fields(program, cols)
