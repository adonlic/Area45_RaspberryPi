from os.path import exists, isfile


# all values are validated as case_sensitive = False, except directory/file path
def is_not_empty(value):
    if value != '':
        return True, None

    return False, "Missing value"


def is_boolean(value):
    ok, message = is_not_empty(value)

    if ok:
        if value.lower() in ['true', 'false']:
            return True, None
        # if value is not valid...
        return False, "Must be boolean value (true, false)"

    return False, message


def is_integer(value):
    ok, message = is_not_empty(value)

    if ok:
        for v in value:
            if '0' > v or '9' < v:
                return False, "Must be integer value"
        return True, None

    return False, message


# float/double value check
def is_double(value):
    ok, message = is_not_empty(value)

    if ok:
        dot_found = False
        message_false = "Must be float/double value"

        for v in value:
            if v == '.':
                if dot_found:
                    return False, "{}, {}".format(message_false, "only one dot is allowed")
                dot_found = True
            elif '0' > v or '9' < v:
                return False, "{}, {}".format(message_false, "unrecognized character detected")

        if value[-1] == '.':
            return False, "{}, {}".format(message_false, "missing digit/s behind dot")
        elif not dot_found:
            return False, "{}, {}".format(message_false, "dot is missing")
        return True, None

    return False, message


def is_filename(value):
    ok, message = is_not_empty(value)

    if ok:
        if exists(value):
            if isfile(value):
                return True, None
            return False, "Must be path to a file"
        return False, "Given path doesn't exist"

    return False, message


def is_directory(value):
    ok, message = is_not_empty(value)

    if ok:
        if exists(value):
            return True, None
        return False, "Given path doesn't exist"

    return False, message


def is_config(value):
    ok, message = is_filename(value)

    if ok:
        # check if it's file with extension 'ini' (config file)
        ext = value.split('.')[-1].lower()

        if ext == 'ini':
            return True, None
        return False, "Must be config file of type INI (*.ini)"

    return False, message


# def is_db(value):
#     ok, message = is_filename(value)
#
#     if ok:
#         # check if it's file with extension 'db' (database file)
#         ext = value.split('.')[-1].lower()
#
#         if ext == 'db':
#             return True, None
#         return False, "Must be database file of type DB (*.db)"
#
#     return False, message


def is_db(value):
    # take all except last one (except filename)
    value_to_dir = '\\'.join(value.split('\\')[:-1])

    if value_to_dir == '':
        value_to_dir = value

    ok, message = is_directory(value_to_dir)

    if ok:
        dot_sides = value.split('.')

        if len(dot_sides) > 1:
            if dot_sides[-2][-1] == '\\':
                return False, "Filename required"
        else:
            if dot_sides[-1] == '\\':
                return False, "Filename required"

        # check if it's file with extension 'db' (database file)
        ext = dot_sides[-1].lower()

        if ext == 'db':
            return True, None
        return False, "Must be database file of type DB (*.db)"

    return False, message


def is_log(value):
    # log method is more special than is_config and is_db because user provides log
    # file name that doesn't exist, it's base for building proper logging file and
    # function is looking for directory existence only (in wider spectre)...

    # take all except last one (except filename)
    value_to_dir = '\\'.join(value.split('\\')[:-1])

    # if it doesn't look like path, then value_to_dir will be empty string...
    if value_to_dir == '':
        value_to_dir = value

    ok, message = is_directory(value_to_dir)

    if ok:
        dot_sides = value.split('.')
        # check if filename exists (from left-to-dot part take last character and
        # see if it's not backslash)
        # ps. there can be more dots, but only last one divides extension from the
        # rest of path
        # (check if there's dot at all)
        if len(dot_sides) > 1:
            if dot_sides[-2][-1] == '\\':
                return False, "Filename required"
        else:
            if dot_sides[-1] == '\\':
                return False, "Filename required"
        # check if it's file with extension 'log' (log file)
        ext = dot_sides[-1].lower()

        if ext == 'log':
            return True, None
        return False, "Must be log file of type LOG (*.log)"

    return False, message


def is_one_of_values(value, valid_values):
    ok, message = is_not_empty(value)
    value = value.lower()
    valid_values_lower = list()

    if ok:
        for valid_value in valid_values:
            # compare as case un-sensitive and use lowercase valid_values for message (new
            # list of lowercase letters is used so lower() function is called only once)
            valid_value_lower = valid_value.lower()
            valid_values_lower.append(valid_value_lower)

            if value == valid_value_lower:
                # return true at first appearance of valid value, because it is
                return True, None
        return False, "Must be one specific value ({})".format(", ".join(valid_values_lower))

    return False, message


def is_file_size(value):
    ok, message = is_not_empty(value)
    is_unit = False
    first_unit_letter = ''
    is_done = False

    if ok:
        for v in value:
            # check if value has too many characters (characters after unit declaration)
            # example: 500kbb, 500bmb etc.
            if is_done:
                return False, "Invalid value (too many characters after declaring unit)"
            # if not case sensitive, size unit have big and/or small chars
            v = v.lower()
            if not is_unit and '0' <= v <= '9':
                continue
            elif not is_unit and v == 'b':
                # expecting end
                is_unit = True
                is_done = True
                continue
            elif not is_unit and v in ['k', 'm']:
                # expecting 'b' letter so it can be kb or mb...
                is_unit = True
                first_unit_letter = v
                continue
            elif is_unit and first_unit_letter in ['k', 'm'] and v == 'b':
                # if function is on unit part and it expects to be 'kb' or 'mb', it's
                # supposed to be end of value...
                is_done = True
                continue
            else:
                # if value parsing was wrong...
                return False, "Must be value with format <integer><unit> where unit can" \
                              "be in bytes, kilobytes or megabytes (b, kb, mb)"
        if is_done:
            return True, None
        # function will go here if there's only integer part
        return False, "Missing unit declaration (b, kb, mb)"

    return False, message


def is_time_after(value):
    return True


def is_time_at(value):
    return True
