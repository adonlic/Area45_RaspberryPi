import os
from configparser import ConfigParser, ParsingError


class ConfigRestriction:
    # all values and keys are lowered in constructor and methods

    def __init__(self, required, validator_func, *valid_values):
        self.required = required
        if not required:
            self.depends_on = dict()
            self.__and_dependency_relations = list()
            self.__or_dependency_relations = list()
        self.__exclusionary_keys = list()
        self.validator_func = validator_func
        self.valid_values = list([value.lower() for value in valid_values])

    def add_dependence(self, key, *values):
        # none, one or more some other key's value/s are possible for current key...
        # for example: logger has 'rotate' key which requires 'depends_on' key and its
        # values 'size' or 'time', but 'depends_on' has one more value too ('nothing'),
        # some other keys just require some other key's presence in config to work, like
        # 'prefix' key needs 'unique_name_source' OR 'name' keys...

        self.depends_on[key] = list([value.lower() for value in values])

        return self

    def add_dependency_and(self, *keys):
        """
        Dependencies that are depending on each other (all given dependencies
        must be used for current config key/option to work).

        :param keys:
        :return:
        """

        self.__and_dependency_relations.append(list([key.lower() for key in keys]))

        return self

    def add_dependency_or(self, *keys):
        """
        Dependencies that exclude one another (only one given dependency can
        exist as key/option in config for current key to work)

        :param keys:
        :return:
        """

        self.__or_dependency_relations.append(list([key.lower() for key in keys]))

        return self

    def add_exclusionary_keys(self, *keys):
        # they counteract each other (list of lists)
        self.__exclusionary_keys = list([key.lower() for key in keys])

        return self

    def get_dependency_and(self, key):
        dependency_and = list()

        for key_set in self.__and_dependency_relations:
            temp_key_set = key_set[:]

            if key in key_set:
                temp_key_set.remove(key)
                for temp_key in temp_key_set:
                    if temp_key not in dependency_and:
                        dependency_and.append(temp_key)

        return dependency_and

    def get_dependency_or(self, key):
        dependency_or = list()

        for key_set in self.__or_dependency_relations:
            # temp_key_set = key_set # DON'T USE THIS! XD
            temp_key_set = key_set[:]

            if key in key_set:
                temp_key_set.remove(key)
                for temp_key in temp_key_set:
                    if temp_key not in dependency_or:
                        dependency_or.append(temp_key)

        return dependency_or

    @property
    def and_dependency_relations(self):
        return self.__and_dependency_relations

    @property
    def or_dependency_relations(self):
        return self.__or_dependency_relations

    def has_or_dependency_relation(self, key):
        for key_set in self.__or_dependency_relations:
            if key in key_set:
                return True

        return False

    @property
    def exclusionary_keys(self):
        return self.__exclusionary_keys


class ConfigManager:
    __instance = None

    @staticmethod
    def init():
        ConfigManager.__instance = ConfigManager()

    @staticmethod
    def get_instance():
        if ConfigManager.__instance is None:
            ConfigManager.__instance = ConfigManager()

        return ConfigManager.__instance

    def read(self, conf_dir, config_structure):
        dot_sides = conf_dir.split('.')

        # if there's at least one dot
        if len(dot_sides) > 1:
            # conf_dir is already config file (shared)
            config_path = conf_dir
        else:
            # conf_dir is directory (mqtt, web)
            config_path = conf_dir + '\config.ini'

        if os.path.exists(config_path):
            config = {}
            parse_phase_one_succeeded = True
            message_for_phase_one = "CONFIG PARSING ERROR (invalid data format): {}".format(config_path)
            parser = ConfigParser()

            try:
                parser.read(config_path)
            except ParsingError:
                parse_phase_one_succeeded = False

            if parse_phase_one_succeeded:
                ok, message = self.__validate(parser, config_structure)

                if ok:
                    for section in parser.sections():
                        for option in parser.options(section):
                            # lowercase key values are must have for right comparison!
                            config[option] = parser[section][option].lower()

                    return config, "Config '{}' loaded".format(config_path)
                else:
                    # invalid config parsing phase two
                    return None, message
            # else phase one was unsuccessful
            return None, message_for_phase_one

        # missing config (create default config for caller)
        # return self.__build_config(conf_dir, caller)

    def __validate(self, parser, config_structure):
        if len(parser.sections()) == 0 and len(config_structure.keys()) > 0:
            return False, "Config is empty"
        else:
            # if there are some sections in parsed config then real config could be less in size or equal, so in
            # any case, it'll bring up error if something's wrong with parsed file

            for section in parser.sections():
                if section in config_structure.keys():
                    # initialization and reset of used_options for each section
                    used_options = list()

                    # region PARSE OPTIONS/KEYS
                    for option in parser.options(section):
                        if option in config_structure[section].keys():
                            option_restriction = config_structure[section][option]

                            # if key is required, then it doesn't have dependencies, but can have excluding keys
                            # if key's not required, it can be optional if it overrides default value and it can
                            # be optional with dependencies if some other key is required to work with...in both
                            # cases it can have excluding keys too and dependencies can exclude one another or
                            # must exist in some group

                            # region FIND EXCLUSIONARY KEYS
                            # exclusionary keys that are found in loaded config file (finds exclusionary keys
                            # immediately after recognizing some key has them)
                            file_exclusionary_keys = list()

                            for exclusionary_key in option_restriction.exclusionary_keys:
                                if exclusionary_key in parser.options(section):
                                    file_exclusionary_keys.append(exclusionary_key)
                            if len(file_exclusionary_keys) > 0:
                                return False, "Key '{}' can't work with '{}' key/s in section '{}'"\
                                    .format(option, ", ".join(file_exclusionary_keys), section)
                            # endregion

                            # region FIND DEPENDENCIES
                            # only options that are not required have dependencies
                            if not option_restriction.required:
                                # check if all dependencies are valid (their relations, value etc.)
                                for key, values in option_restriction.depends_on.items():
                                    # if not in config file and if in config file...
                                    if key not in parser.options(section):
                                        # if dependency is not in config file, check if it has any OR relations
                                        # with other keys in same section and if it does, missing key can be
                                        # exception if some other key can be used instead...
                                        # everything else is not valid
                                        if option_restriction.has_or_dependency_relation(key):
                                            exclusionary_dependencies = option_restriction.get_dependency_or(key)
                                            detected_in_config = 0

                                            # so, this key has OR relation but is not used as option/key, and
                                            # next step is to see if other keys exist at all, is there too many
                                            # exclusionary dependencies or is there just one as it's supposed
                                            # to be
                                            for exclusionary_dependency in exclusionary_dependencies:
                                                if exclusionary_dependency in parser.options(section):
                                                    detected_in_config += 1

                                            if detected_in_config == 1:
                                                continue
                                            elif detected_in_config > 1:
                                                # don't forget to add current key as possible option with other
                                                # exclusionary keys...
                                                exclusionary_dependencies.append(key)
                                                return False, "Exclusionary dependencies detected for key '{}' " \
                                                              "in section '{}', use only one of: {}"\
                                                    .format(option, section, ", ".join(exclusionary_dependencies))

                                        return False, "Dependency is missing for key '{}' in section '{}': {} " \
                                                      "(other dependencies: {})"\
                                            .format(option, section, key,
                                                    ", ".join(option_restriction.depends_on.keys()))
                                    else:
                                        # anything that went here is right, except if it's key that has OR
                                        # relation and one of them is already there, that's why other keys from
                                        # same relation will be tested to stop further parsing if anything's not
                                        # right...
                                        if option_restriction.has_or_dependency_relation(key):
                                            exclusionary_dependencies = option_restriction.get_dependency_or(key)

                                            for exclusionary_dependency in exclusionary_dependencies:
                                                if exclusionary_dependency in parser.options(section):
                                                    # as this key is already from same OR relation, any other key
                                                    # is not valid!
                                                    exclusionary_dependencies.append(key)
                                                    return False, "Exclusionary dependencies detected for key '{}' " \
                                                                  "in section '{}', use only one of: {}"\
                                                        .format(option, section, ", ".join(exclusionary_dependencies))

                                        # check value of current dependency, if current key/option requires
                                        # specific dependency value (not all keys can be used just with relation
                                        # restrictions, sometimes they require special behavior)
                                        if len(values) > 0:
                                            if (parser.get(section, key)).lower() not in values:
                                                return False, "Dependency '{}' for key '{}' in section '{}' has " \
                                                              "invalid value and key can't be used, remove/change " \
                                                              "key or change dependency value. Dependency value/s " \
                                                              "required for key to work: {}"\
                                                    .format(key, option, section, ", ".join(values))
                            # endregion

                            # region VALIDATE KEY'S VALUE
                            # if key setup is ok for this key, check if value is ok
                            if len(option_restriction.valid_values) == 0:
                                ok, message = option_restriction.validator_func(parser.get(section, option))
                            else:
                                ok, message = option_restriction.validator_func(
                                    parser.get(section, option), option_restriction.valid_values)
                            if not ok:
                                return False, "{} for key '{}' at section '{}'".format(message, option, section)
                            # if value is ok, take next key/section
                            # endregion

                            # remove validated keys from dict so it can be compared later if some of them are
                            # missing...it can't be done yet because some keys are required for dependency
                            # evaluation, that's why it'll be written in special list...
                            used_options.append(option)
                        else:
                            return False, "Unknown key '{}' in section '{}'".format(option, section)
                    # endregion

                    # region FIND MISSING KEYS IF THEY EXIST
                    # remove section from config structure so we can later detect if some section/s is/are missing
                    # by looking if it's empty or not (empty = all sections are checked, none is missing)
                    # not used options => difference between valid config and given config
                    not_used_options = list(set(config_structure[section].keys()) - set(parser.options(section)))
                    keys_missing = list()
                    # REMEMBER: not_used_options can have required and optional keys, keys_missing have only
                    # required...

                    for not_used in not_used_options:
                        option_restriction = config_structure[section][not_used]
                        is_missing = True

                        # check only required keys that are not used and are not part of dependencies (in not_used
                        # will go keys/options that user didn't put and which other user's keys didn't use as
                        # dependencies)
                        if option_restriction.required:
                            for used in used_options:
                                # if current not_used key is not used because one of its exclusionary keys is used,
                                # then it's ok (it's checked previously)
                                # if it's not used but it doesn't have used exclusionary keys, then it's not ok
                                if used in option_restriction.exclusionary_keys:
                                    # it's ok that it's not in config...
                                    not_used_options.remove(not_used)
                                    is_missing = False
                                    break

                            # if it's missing...ERROR
                            if is_missing:
                                keys_missing.append(not_used)

                    # remove structure only if all is ok
                    if len(keys_missing) == 0:
                        del config_structure[section]
                    else:
                        # to_delete list must be used so we don't delete object while iterating!
                        to_delete = list()

                        for conf_key in config_structure[section].keys():
                            # remove from config structure only keys that are not put in keys_missing (must notify
                            # user later which keys are missing)
                            if conf_key not in keys_missing:
                                to_delete.append(conf_key)
                        for del_key in to_delete:
                            del config_structure[section][del_key]
                    # endregion
                else:
                    return False, "Unknown section '{}'".format(section)

            # if keys or sections are missing, write them down
            error_message_missing = "Config is not valid, missing:\n"

            for section in config_structure.keys():
                # when whole section is missing, it'll show all required, but when session tag is missing too, it'll
                # show even optional attributes!
                error_message_missing += "\tSECTION {}: {}".format(section, ", ".join(config_structure[section].keys()))

            # if there are some missing items in config...
            if len(config_structure.keys()) > 0:
                return False, error_message_missing

        return True, None

    def __build_config(self):
        pass


class ConfigCache:
    """
    Stores all loaded config file's options in key value format. That means that every
    option/key in config files must be unique even from other sections.
    For example, if one file has section Section1 and key Key1 and other section Section2
    has key Key1 too, it's forbidden. Same goes if config file ConfigFile1 has key Key1
    somewhere and other config file ConfigFile2 has key Key1 somewhere too...
    """

    __instance = None

    @staticmethod
    def init():
        ConfigCache.__instance = ConfigCache()

    @staticmethod
    def get_instance():
        if ConfigCache.__instance is None:
            ConfigCache.__instance = ConfigCache()

        return ConfigCache.__instance

    def __init__(self):
        self.__global_conf = None
        self.__conf = None

    def load(self, global_conf, conf):
        self.__global_conf = global_conf
        self.__conf = conf

    @property
    def global_config(self):
        return self.__global_conf

    @property
    def config(self):
        return self.__conf
