import os

import Identicon

from . import app


def ensure_identicon(tripcode: str) -> str:
    """Make sure tripcode has an associated identicon.

    The identicon is a file saved in static/identicons/
    with the filename matching the tripcode.

    If no such file exists it will be created.

    Returns:
        str: the path to the identicon.

    """

    directory_where_identicons_go = os.path.join(
        app.app.static_folder,
        'identicons',
    )
    if not os.path.exists(directory_where_identicons_go):
        os.makedirs(directory_where_identicons_go)

    path_where_identicon_should_be = os.path.join(
        directory_where_identicons_go,
        tripcode + '.png',
    )

    if not os.path.isfile(path_where_identicon_should_be):
        identicon = Identicon.render(tripcode)
        with open(path_where_identicon_should_be, 'wb') as f:
            f.write(identicon)

    return path_where_identicon_should_be
