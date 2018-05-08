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
