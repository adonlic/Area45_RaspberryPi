import netifaces


"""
Methods that provide basic info about computer and project's structure. It supplies
callers (other scripts) with information they wouldn't know, because they're dynamic.
For example, caller can have different position in project structure.
"""


def get_shared_folder(caller_work_dir):
    """
    Returns default shared folder path. It's first used to find mutual config (for MQTT
    client and web server).

    :param caller_work_dir: any directory below rpi directory
    :return:                absolute path to project's shared folder
    """

    dirs = caller_work_dir.split('\\')
    dirs = dirs[:dirs.index('rpi') + 1]
    dirs.append('shared')

    return '\\'.join(dirs)


def get_databases_folder(caller_work_dir):
    """
    Returns default databases folder path. As MQTT client and web server share node data,
    it's default position of its mutual databases.

    :param caller_work_dir: any directory below rpi directory
    :return:                absolute path to project's databases folder
    """

    dirs = caller_work_dir.split('\\')
    dirs = dirs[:dirs.index('rpi') + 1]
    dirs.append('shared')
    dirs.append('data')
    dirs.append('databases')

    return '\\'.join(dirs)


def get_mac(local_address, local_address_type):
    """
    Returns MAC address used to identify MQTT client and web server. It works
    cross-platform and currently are supported IPv4 and IPv6. To work, there must be
    network interface that's currently active (given address must exist and it has to
    have MAC address by its side).

    :param local_address:       one of computer network interface addresses (IPv4, IPv6)
    :param local_address_type:  integer (if it looks for IPv4, code 2, if IPv6, code 23)
    :return:                    list containing MAC address or None as first parameter
                                and message as result of search)
    """

    # get network interfaces
    for i in netifaces.interfaces():
        # get its addresses (MAC, IPv4, IPv6...)
        addresses = netifaces.ifaddresses(i)

        try:
            # does current interface have IPv4 (2) or IPv6 (23)?
            if int(local_address_type) == netifaces.AF_INET:
                address = addresses[netifaces.AF_INET][0]['addr']
            elif int(local_address_type) == netifaces.AF_INET6:
                address = addresses[netifaces.AF_INET6][0]['addr']
            else:
                raise NotImplementedError
        except (KeyError, IndexError):
            # current interface doesn't have targeted address type
            continue
        except NotImplementedError:
            # targeted address type is not supported
            return None, "Unsupported address type, try with IPv4 or IPv6 (codes 2 and 23)"

        # is it local address that AP knows about? (AP = Access Point)
        if address == local_address:
            return addresses[netifaces.AF_LINK][0]['addr'], "Address found ({})"\
                .format(addresses[netifaces.AF_LINK][0]['addr'])

    # if couldn't find interface with targeted address, return None
    return None, "Couldn't find network interface with given address (local address doesn't exist or there's " \
                 "no internet)"
