# TODO: move all the model stuff that's templating into here
import re

from flask import request

from . import models


TRUNCATE_LENGTH = 140


def truncate(some_string: str, length: int = TRUNCATE_LENGTH):
    if len(some_string) > length:
        return some_string[:length] + '&hellip;'
    else:
        return some_string


def get_stylesheet():
    return request.cookies.get('stylesheet_url')


def get_pages():
    return models.db.session.query(models.Page).all()


def get_blotter_entries():
    return models.BlotterEntry.query.order_by(models.BlotterEntry.id.desc()).all()


# FIXME: rename to "contrast text" or something
# TODO: the brightness factor...
def complementary_color(my_hex):
    """Returns maximal contrast color to provided.

    Example:
    >>>complementaryColor('FFFFFF')
    '000000'

    """

    if my_hex[0] == '#':
        my_hex = my_hex[1:]

    my_hex_number = int(my_hex, 16)
    absolute_grey = int('ffffff', 16) / 2

    if my_hex_number > absolute_grey:
        return '000000'
    elif my_hex_number == absolute_grey:
        return '000000'
    else:
        return 'ffffff'


def since_bumptime(bumptime, thread=None, reply=None):
    total_seconds = int((bumptime.now() - bumptime).total_seconds())
    days, seconds = divmod(total_seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    pairs = (
        (days, 'Day'),
        (hours, 'Hour'),
        (minutes, 'Minute'),
        (seconds, 'Second'),
    )
    parts = []
    for value, unit_singular in pairs:
        if value:
            output = '%d %s' % (value, unit_singular)
            if value > 1:
                output += 's'
            parts.append(output)

    if parts:
        very_readable = parts[0]
    else:
        very_readable = 'now'

    datetime_w3c_spec = str(bumptime)[:-3]

    if thread:
        permalink = '<a href="/threads/{permalink}">{parts} ago</a>'.format(
            permalink='%d#%d' % (thread, reply) if reply else thread,
            parts=very_readable,
        )
    elif reply:
        raise Exception('heck no!')
    else:
        permalink = very_readable + ' ago'

    return '''
    <time datetime="{bumptime}" title="{bumptime}">
    {permalink} 
    </time>
    '''.format(bumptime=datetime_w3c_spec, permalink=permalink)
