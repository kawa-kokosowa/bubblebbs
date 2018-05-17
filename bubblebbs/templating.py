# TODO: move all the model stuff that's templating into here
import re

from . import models


def get_pages():
    return models.db.session.query(models.Page).all()


def get_blotter_entries():
    return models.BlotterEntry.query.order_by(models.BlotterEntry.id.desc()).all()


def word_filter(message):
    word_filters = models.db.session.query(models.WordFilter).all()
    for word_filter in word_filters:
        find = re.compile(r'\b' + re.escape(word_filter.find) + r'\b', re.IGNORECASE)
        message = find.sub(word_filter.replace, message)
    return message


def complementary_color(my_hex):
    """Returns complementary RGB color

    Example:
    >>>complementaryColor('FFFFFF')
    '000000'
    """
    if my_hex[0] == '#':
        my_hex = my_hex[1:]
    rgb = (my_hex[0:2], my_hex[2:4], my_hex[4:6])
    comp = ['%02X' % (255 - int(a, 16)) for a in rgb]
    return ''.join(comp)


def since_bumptime(bumptime):
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

    very_readable = ', '.join(parts)
    if not very_readable:
        very_readable = 'now'

    datetime_w3c_spec = str(bumptime)[:-3]
    return '''
    <time datetime="{bumptime}" title="{bumptime}">
    {parts}
    </time>
    '''.format(bumptime=datetime_w3c_spec, parts=very_readable)
