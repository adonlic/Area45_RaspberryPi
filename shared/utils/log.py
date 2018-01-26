from datetime import datetime
from os.path import exists, getsize
from os import remove


class Logger:
    __instance = None
    DEPENDS_ON_NOTHING = 0
    DEPENDS_ON_SIZE = 1
    DEPENDS_ON_TIME = 2

    @staticmethod
    def get_instance():
        return Logger.__instance

    def __init__(self, name, filename='', depends_on=DEPENDS_ON_NOTHING,
                 max_file_size='', time_after='', time_at='', max_files=1, rotate=False,
                 has_buffer=False, max_buffer_size='',
                 parent=None, print_log=False):
        self.__name = name

        if filename != '':
            self.__to_file = True
            self.__filename = filename
            # temp_filename keeps current active file with datetime (newest file of filename)
            self.__temp_filename = filename
            self.__depends_on = depends_on

            if depends_on == Logger.DEPENDS_ON_SIZE:
                self.__max_file_size = Logger.__convert_to_bytes(max_file_size)
            else:
                # else it depends on time...
                self.__time_after = Logger.__convert_to_seconds(time_after)
                self.__time_at = time_at

            self.__max_files = max_files
            self.__rotate = rotate
            if rotate:
                self.__files = list()
        else:
            self.__to_file = False

        self.__print_log = print_log

        if has_buffer:
            self.__buffer = list()

        # create only one instance
        Logger.__instance = self

    @staticmethod
    def __convert_to_bytes(size):
        # get last 2 chars...
        size_value_str = ''
        size_unit = ''

        for char in size:
            if '0' <= char <= '9':
                size_value_str += char
            else:
                char = char.upper()

                size_unit += char

        size_value = int(size_value_str)

        if size_unit == 'B':
            return size_value
        elif size_unit == 'KB':
            return size_value * 1024

        # else it's in MB
        return size_value * 1024 * 1024

    @staticmethod
    def __convert_to_seconds(countdown_time):
        seconds = 0
        time_value = ''

        for char in countdown_time:
            if '0' <= char <= '9':
                time_value += char
            else:
                char = char.upper()

                if char == 'W':
                    seconds += int(time_value) * 60 * 60 * 24 * 7
                elif char == 'D':
                    seconds += int(time_value) * 60 * 60 * 24
                elif char == 'H':
                    seconds += int(time_value) * 60 * 60
                elif char == 'M':
                    seconds += int(time_value) * 60
                else:
                    # else it's in seconds
                    seconds += int(time_value)

                time_value = ''

        return seconds

    def info(self, message):
        # build short messages for print...
        record = self.__build_record('INFO', message)

        if self.__print_log:
            print(record)
        if self.__to_file:
            self.__write_to_file(record)

    def warning(self, message):
        record = self.__build_record('WARNING', message)

        if self.__print_log:
            print(record)
        if self.__to_file:
            self.__write_to_file(record)

    def error(self, message):
        record = self.__build_record('ERROR', message)

        if self.__print_log:
            print(record)
        if self.__to_file:
            self.__write_to_file(record)

    def __build_record(self, message_type, message):
        return '{}\t\t{}\t\t{}{}'.format(
            Logger.__get_str_formatted_datetime(), message_type, self.__get_name_correction(), message)

    @staticmethod
    def __get_str_formatted_datetime():
        """
        Returns current date and time.
        Result example:
            2017-12-25 23:30:05

        :return:    datetime string
        """

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def __get_str_formatted_datetime2():
        """
        Returns current date and time, compatibile with folder naming conventions.
        Result example:
            2017-12-25_23-30-05

        :return:    datetime string
        """

        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def __get_name_correction(self):
        # returns name with spaces to align with other records...
        name_n_space = self.__name
        # space for name has size of 24 chars...
        chars_left = 24 - len(self.__name)

        for i in range(chars_left):
            name_n_space += ' '

        return name_n_space

    def __write_to_file(self, record):
        if not exists(self.__temp_filename):
            # add datetime to filename
            self.__temp_filename = self.__new_filename()

            if self.__depends_on == Logger.DEPENDS_ON_SIZE and self.__rotate:
                self.__files.append(self.__temp_filename)
        record += '\n'
        write_to_file = True

        if self.__depends_on == Logger.DEPENDS_ON_SIZE:
            if exists(self.__temp_filename):
                if getsize(self.__temp_filename) + Logger.__get_byte_size(record) > self.__max_file_size:
                    # make temp for temp because it can happen it adds new record in same
                    # file only because of same filename (logger logs messages too fast)...
                    temp_filename = self.__new_filename()

                    if self.__temp_filename == temp_filename:
                        self.__temp_filename = self.__new_filename2(self.__temp_filename)
                    else:
                        self.__temp_filename = temp_filename

                    if self.__rotate:
                        # if max number of filex exceed -> rotate by using oldest one
                        if self.__max_files == len(self.__files):
                            oldest_file = self.__find_oldest_in_files()
                            self.__files.remove(oldest_file)
                            if exists(oldest_file):
                                remove(oldest_file)
                        self.__files.append(self.__temp_filename)
            elif Logger.__get_byte_size(record) > self.__max_file_size:
                # if file doesn't exist, it'll try to add new record but we must check if
                # it has valid size too (this can occur if max file size is too small or
                # record is too big)
                write_to_file = False

        if write_to_file:
            file = open(self.__temp_filename, 'a')
            file.write(record)
            file.close()

    def __new_filename(self):
        path = self.__filename.split('/')
        file = path[-1].split('.')

        return '{}_{}.{}'.format(file[0], Logger.__get_str_formatted_datetime2(), file[1])

    def __new_filename2(self, old_filename):
        # create new copy of file with same name...
        path = old_filename.split('/')
        file = path[-1].split('.')
        copy_number_str = '1'

        if file[0][-1] == ')':
            start_index = file[0].find('(')
            copy_number = int(file[0][start_index + 1:-1])
            copy_number_str = str(copy_number + 1)

        original_old_filename_part = old_filename[:old_filename.find('.')]

        return '{}({}).{}'.format(original_old_filename_part, copy_number_str, file[1])

    @staticmethod
    def __get_byte_size(record):
        return len(record)

    def __find_oldest_in_files(self):
        # first file is the oldest, now compare
        oldest = self.__files[0]

        # this will work if there are at least 2 files (it's called when using rotation
        # mode, but user should know rotation mode is useless with max_files = 1...)
        for i in range(1, len(self.__files)):
            if oldest > self.__files[i]:
                oldest = self.__files[i]

        return oldest
