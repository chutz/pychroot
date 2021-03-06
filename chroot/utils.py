import errno
import logging
import os

from subprocess import call


def dictbool(dct, key):
    """Check if a key exists and is True in a dictionary.

    :param dct: The dictionary to check.
    :type dct: dict
    :param key: The key to check
    :type key: any
    """
    return key in dct and isinstance(dct[key], bool) and dct[key]


def getlogger(log, name):
    """Gets a logger given a logger and a package.

    Will return the given logger if the name is not generated from
    the current package, otherwise generate a logger based on __name__.

    :param log: Logger to start with.
    :type log: logging.Logger
    :param name: The __name__ of the caller.
    :type name: str
    """
    return (
        log if isinstance(log, logging.Logger)
        and not log.name.startswith(name.partition('.')[0])
        else logging.getLogger(name))


def bind(src, dest, create=False, log=None, recursive=False, readonly=False, **_kwargs):
    """Set up a bind mount.

    :param src: The source location to mount.
    :type src: str
    :param dest: The destination to mount on.
    :type dest: str
    :param create: Whether to create the destination.
    :type create: bool
    :param log: A logger to use for logging.
    :type log: logging.Logger
    :param recursive: Whether to use a recursive bind mount.
    :type recursive: bool
    :param readonly: Whether to mount readonly.
    :type readonly: bool
    """
    log = getlogger(log, __name__)
    if src not in ['proc', 'sysfs', 'tmpfs']:
        src = os.path.realpath(src)
    dest = os.path.realpath(dest)

    if create:
        try:
            if not os.path.isdir(src) and src not in ['proc', 'sysfs', 'tmpfs']:
                os.makedirs(os.path.dirname(dest))
            else:
                os.makedirs(dest)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        if not os.path.isdir(src) and src not in ['proc', 'sysfs', 'tmpfs']:
            open(dest, 'w').close()

    if not os.path.exists(src) and src not in ['proc', 'sysfs', 'tmpfs']:
        raise MountError('Attempt to bind mount nonexistent source path "{}"'.format(src))
    elif not os.path.exists(dest):
        raise MountError('Attempt to bind mount on nonexistent path "{}"'.format(dest))

    if src in ['proc', 'sysfs', 'tmpfs']:
        status = call(['mount', '--no-mtab', '-t', src, src, dest])
    else:
        # do the bind mount by shelling out to mount
        log.debug("  Bind mounting '{}' on '{}'".format(src, dest))
        status = call(['mount', '--no-mtab', '--rbind' if recursive else '--bind', src, dest])

    if status != 0:
        raise MountError('Mount failed')

    # remount read-only if read-only was requested
    if readonly:
        if call(['mount', '--no-mtab', '--rbind' if recursive else '--bind', '--options', 'remount,ro', dest]) != 0:
            raise MountError('Mount failed')


class MountError(Exception):

    """Exception that is raised when there is an error creating a bind mount."""
    pass


# vim:et:ts=4:sw=4:tw=120:sts=4:ai:
