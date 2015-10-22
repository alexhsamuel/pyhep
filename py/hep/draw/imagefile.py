#-----------------------------------------------------------------------
#
# imagefile.py
#
# Copyright (C) 2005 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Function to render a figure to a bitmap file."""

#-----------------------------------------------------------------------
# includes
#-----------------------------------------------------------------------

from   hep.draw import *
from   hep.draw.xwindow import _ImageFile

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def render(figure, path, size=None, virtual_size=None,
           resolution=75/inch):
    """Render 'figure' as an image file to 'path'.

    'figure' -- The figure to render.

    'path' -- The path to the image file to save to.

    'size' -- The size in pixels of the saved image.

    'virtual_size' -- The virtual size of the figure.

    'resolution' -- Conversion from virtual size to pixels.  If one of
    'size' or 'virtual_size' is omitted or 'None', the it is computed
    from the other using this value."""

    if size is None:
        if virtual_size is None:
            # One of 'size' and 'virtual_size' must be specified.
            raise ValueError, "indeterminate image size"
        # Compute the virtual size.
        vx, vy = virtual_size
        sx, sy = vx * resolution, vy * resolution
    else:
        sx, sy = size

    # Convert pixel sizes to integers.
    sx, sy = int(sx), int(sy)
    # Perform sanity checks.
    if sx < 1 or sy < 1:
        raise ValueError, "image size must be positive"

    if virtual_size is None:
        virtual_size = sx / resolution, sy / resolution
    
    image_file = _ImageFile((sx, sy), virtual_size)
    image_file.render(figure)
    image_file.save(path)


