#-----------------------------------------------------------------------
#
# plot.py
#
# Copyright (C) 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Plotting classes for histograms."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division
from __future__ import generators

from   hep.draw import *
from   hep.draw import latex
import hep.fn
from   hep.hist import *
import hep.hist.function
from   hep import modified
import hep.num
from   hep.text import formatNumber
from   hep.xml_util import *
from   math import *

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

default_positive_color = Color(0.200, 0.200, 0.200)
default_negative_color = Color(0.700, 0.420, 0.543)
default_overrun_color =  Color(0.400, 0.000, 0.000)
default_underrun_color = Color(1.000, 0.900, 0.945)
default_overflow_margin = 0.005
default_overflow_size = 0.005
default_thickness = 0.75 * point

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Axis(Figure):

    axis = modified.Property("axis")


    def __init__(self, axis, orientation, **style):
        if orientation not in ("x", "y"):
            raise ValueError, "unknown orientation '%s'" % orientation

        self.axis = axis
        self.orientation = orientation
        Figure.__init__(self, style)
        self.watch_modified.append(axis)


    def _render(self, renderer, region, **style):
        style.update(self.style)

        axis = self.axis
        orientation = self.orientation

        # Extract styles.  For style "foo", we first look for
        # "x_axis_foo" or "y_axis_foo", depending on the orientation.
        # If that is not present, we look for "foo".  If that is not
        # present, we use the default.
        def getStyle(name, default):
            specific_name = orientation + "_axis_" + name
            return style.get(specific_name, style.get(name, default))

        if orientation == "x":
            default_position = "bottom"
        elif orientation == "y":
            default_position = "left"

        axis_line       = getStyle("line", False)
        axis_thickness  = getStyle("thickness", 0.75 * point)
        log_scale       = getStyle("log_scale", False)
        overflows       = getStyle("overflows", True)
        position        = getStyle("position", default_position)
        color           = getStyle("color", black)
        font_family     = getStyle("font", "Times")
        font_size       = getStyle("font_size", 10 * point)
        ticks           = getStyle("ticks", 5)
        offset          = getStyle("offset", 0.001)
        range           = getStyle("range", axis.range)
        tick_size       = getStyle("tick_size", 0.001)
        tick_thickness  = getStyle("tick_thickness", 0.5 * point)
        axis_label      = getStyle("label", makeAxisLabel(axis))

        # Validate the position.
        if orientation == "x" \
           and position not in ("top", "bottom", None):
            raise ValueError, "invalid position %r" % position
        if orientation == "y" \
           and position not in ("left", "right", None):
            raise ValueError, "invalid position %r" % position

        try:
            # Is 'ticks' a sequence?
            ticks = tuple(ticks)
        except TypeError:
            # No.  Interpret it as the number of ticks to use.
            ticks = chooseTicks(self.axis, range, int(ticks), log_scale)
        else:
            # Yes.  Make sure all ticks lie in the range.
            lo, hi = range
            ticks = [ t for t in ticks if lo <= t < hi ]

        if log_scale:
            range = map(log10, range)
            ticks = map(log10, ticks)

        renderer.color = color
        renderer.dash = None

        ((x0, y0, x1, y1), 
         (x_overflows, y_overflows),
         (xuf, xof, yuf, yof)) = setupOverflows(region, style)

        # Set up coordinates.
        if orientation == "x":
            y0, y1 = region[1], region[3]
            xlo, xhi = range
            if position == "bottom":
                y = y1 - offset
                direction = 1
            elif position == "top":
                y = y0 + offset
                direction = -1
        elif orientation == "y":
            x0, x1 = region[0], region[2]
            ylo, yhi = range
            if position == "left":
                x = x1 - offset
                direction = 1
            elif position == "right":
                x = x0 + offset
                direction = -1

        # Draw the axis line.
        if axis_line:
            renderer.thickness = axis_thickness
            renderer.dash = None

            if orientation == "x":
                renderer.line(((x0, y), (x1, y)))

            elif orientation == "y":
                renderer.line(((x, y0), (x, y1)))

        # Draw the tick marks.
        if tick_size is not None and tick_thickness is not None:
            renderer.thickness = tick_thickness

            if orientation == "x":
                for tick in ticks:
                    x = x0 + (x1 - x0) * (tick - xlo) / (xhi - xlo)
                    renderer.line(((x, y), (x, y - direction * tick_size)))

            elif orientation == "y":
                for tick in ticks:
                    y = y0 + (y1 - y0) * (tick - ylo) / (yhi - ylo)
                    renderer.line(((x, y), (x - direction * tick_size, y)))

        # Draw the tick labels
        if font_family is not None:
            renderer.font = (font_family, font_size)
            formatter = tickLabelFormatter(ticks, style)
            
            if orientation == "x":
                # Compute the bottom position of the tick marks.
                y_tick = y - direction * (tick_size + 0.001)
                y_alignment = (1 + direction) / 2
                # Draw tick labels.
                for tick in ticks:
                    if log_scale:
                        label = formatter(10 ** tick)
                    else:
                        label = formatter(tick)
                    x = x0 + (x1 - x0) * (tick - xlo) / (xhi - xlo)
                    if tick == ticks[0]:
                        x_alignment = 0.2
                    elif tick == ticks[-1]:
                        x_alignment = 0.8
                    else:
                        x_alignment = 0.5
                    renderLatex(renderer, (x, y_tick), label, style,
                                alignment=(x_alignment, y_alignment))
                # Label the underflow and overflow bins, if shown.
                if x_overflows:
                    renderLatex(renderer, (xuf[1], y_tick), "UF", style,
                                alignment=(1, y_alignment))
                    renderLatex(renderer, (xof[0], y_tick), "OF", style,
                                alignment=(0, y_alignment))
                    
            elif orientation == "y":
                # Compute the left position of the tick marks.
                x_tick = x - direction * (tick_size + 0.001)
                alignment = ((1 + direction) / 2, 0.5)
                # Draw tick labels.
                for tick in ticks:
                    if log_scale:
                        label = formatter(10 ** tick)
                    else:
                        label = formatter(tick)
                    y = y0 + (y1 - y0) * (tick - ylo) / (yhi - ylo)
                    renderLatex(renderer, (x_tick, y), label, style,
                                alignment=alignment)
                # Label the underflow and overflow bins, if shown.
                if y_overflows:
                    y = (yuf[0] + yuf[1]) / 2
                    renderLatex(renderer, (x_tick, y), "UF", style,
                                alignment=alignment)
                    y = (yof[0] + yof[1]) / 2
                    renderLatex(renderer, (x_tick, y), "OF", style,
                                alignment=alignment)

        # Label the axis.
        if axis_label is not None and font_family is not None:
            renderer.font = (font_family, font_size)
            if orientation == "x":
                position = (region[2], y_tick - direction * font_size)
                alignment = (1, (1 + direction) / 2)
            elif orientation == "y":
                position = (region[0], region[3])
                alignment = (0, -1)
            renderLatex(renderer, position, axis_label, style,
                        alignment=alignment)



#-----------------------------------------------------------------------

class Histogram1DPlot(Figure):

    def __init__(self, histogram, **style):
        self.histogram = histogram
        Figure.__init__(self, style)
        self.watch_modified.append(histogram)


    def __set_data(self, histogram):
        self.histogram = histogram


    data = property(lambda self: self.histogram, __set_data)


    def getXAxis(self, style):
        return self.histogram.axis


    def getYAxis(self, x_range, style):
        """Concoct a y axis object appropriate for the histogram.

        'x_range' -- The range of x values that are being plotted."""

        style = dict(style)
        style.update(self.style)

        histogram = self.histogram
        axis = histogram.axis
        overflows = style["y_axis_overflows"]
        errors = style["errors"]
        log_scale = style["y_axis_log_scale"]
        bin_width = self._getNormalBinWidth(style)

        # Compute the range of y values corresponding to the x range.
        bin_numbers = hep.hist.AxesIterator(
            histogram.axes, range=(x_range, ), overflows=overflows)
        lo, hi = getBinRange(
            histogram, bin_numbers, errors, log_scale, bin_width)
        # Expand the range a bit.
        lo -= 0.01 * abs(lo)
        hi += 0.01 * abs(hi)

        # Make an unbinned axis with this range.
        axis = hep.hist.Axis(histogram.bin_type, range=(lo, hi))

        # Set the axis label.
        if "y_axis_label" in style:
            axis.label = style["y_axis_label"]
        elif bin_width is not None:
            bin_units = getattr(histogram, "units", "entries")
            axis_units = getattr(histogram.axis, "units", "")
            lo, hi = histogram.axis.range
            axis.label = "%s / %s %s" \
                % (bin_units, formatNumber(bin_width), axis_units)
        else:
            bin_units = getattr(histogram, "units", "entries")
            axis.label = "%s / bin" % bin_units
            
        return axis


    def _getNormalBinWidth(self, style):
        """Return the bin width to use for normalizing bin contents.

        returns -- The bin width to use as the denominator for plotting
        bin contents.  If 'None', bin contents should be displayed
        without normalizing to a fixed bin width."""
        
        bin_size = style.get("normalize_bin_size", "auto")
        if bin_size == "auto":
            # Use the size of the first bin.
            x0, x1 = self.histogram.axis.getBinRange(0)
            bin_size = x1 - x0
        return bin_size


    def _renderBins_skyline(self, renderer, y_map, (lo, hi), style, bin_iter):
        dash = style.get("dash", None)
        errors = style.get("errors", True)
        fill_color = style.get("fill_color", Gray(0.9))
        line_color = style.get("line_color", None)
        thickness = style.get("thickness", default_thickness)
        log_scale = style.get("y_log_scale")
        error_hatch_pitch = style.get("error_hatch_pitch", 0.001)
        error_hatch_thickness = style.get("error_hatch_thickness", 0.00015)
        error_hatch_color = style.get("error_hatch_color", None)

        # Prefer to draw from y of zero.  If zero is not in the y
        # range, draw from the edge of the y range closest to zero.
        if lo > 0:
            y0 = y_map(lo)
        elif hi < 0:
            y0 = y_map(hi)
        else:
            y0 = y_map(0)

        # Collect the verteces of a filled polygon for the histogram
        # contents.
        fill_points = []
        # Collect line segments for of histogram outline.
        outline_points = []
        outline_segments = []
        # Collect position information for error zones.
        error_zones = []
        # Loop over bins.
        first = True
        for (x0, x1), value, error in bin_iter:
            # Construct the first point.
            if first:
                fill_points.append((x0, y0))
                outline_points.append((x0, y0))
                first = False

            # Constrain the value to the range of the histogram.
            v = constrain(value, lo, hi)
            y = y_map(v)

            if fill_color:
                # Collect points for the filled polygon.
                fill_points.append((x0, y))
                fill_points.append((x1, y))

            if line_color:
                # Include the upper-left point.
                outline_points.append((x0, y))
                # Only draw a horizontal line across the top of the bin
                # if it is within the y range and is nonzero.
                if not (lo <= value <= hi):
                    outline_segments.append(outline_points)
                    outline_points = []
                # Continue with or restart from the upper-right point.
                outline_points.append((x1, y))

            if errors and lo <= value <= hi:
                err_lo, err_hi = error
                ylo = y_map(max(lo, value - err_lo))
                yhi = y_map(min(hi, value + err_hi))
                error_zones.append(((x0, x1), (ylo, y, yhi)))

        # Construct the last point.
        if not first:
            fill_points.append((x1, y0))
            outline_points.append((x1, y0))
            outline_segments.append(outline_points)

        # Draw the filled histogram.
        if fill_color:
            renderer.color = fill_color
            renderer.polygon(fill_points)

        # Draw regions hatched with diagonal lines to indicate the
        # errors on the bin contents.
        if errors:
            # Use the specified color, if any, for error hatching.
            if error_hatch_color is not None:
                err_hi_color = error_hatch_color
                err_lo_color = error_hatch_color
            # If the histogram is not filled, just use the line color
            # for the error hatching.
            elif fill_color is None:
                if line_color is None:
                    # No line color either; just use black.
                    err_hi_color = black
                    err_lo_color = black
                else:
                    err_hi_color = line_color
                    err_lo_color = line_color
            # If the histogram is filled, use the fill color for upper
            # errors, and white (drawn over the filled region) for lower
            # errors. 
            else:
                err_hi_color = fill_color
                err_lo_color = white

            pitch = error_hatch_pitch
            renderer.thickness = error_hatch_thickness
            renderer.dash = None
            # Draw the error zones.
            for (x0, x1), (ylo, y, yhi) in error_zones:
                # Draw the hatching for the high error.
                x_min = x0 - (yhi - y)
                x_max = x1
                # Set the phase so that adjacent hatched regions line up.
                x_min += pitch - (x_min - y) % pitch
                x_max += pitch - (x_max - y) % pitch
                if y > y0:
                    renderer.color = err_hi_color
                else:
                    renderer.color = err_lo_color
                # Loop over hatch lines.
                for x in hep.num.range(x_min, x_max, pitch):
                    # Crop the hatch line to the bin area.
                    d0 = max(0, x0 - x)
                    d1 = max(0, min(yhi - y, x1 - x))
                    if d0 == d1:
                        continue
                    renderer.line(
                        ((x + d0, y + d0), (x + d1, y + d1)))

                # Draw the hatching for the lower error.
                x_min = x0 - (yhi - y)
                x_max = x1
                # Set the phase so that adjacent hatched regions line up.
                x_min += pitch - (x_min - ylo) % pitch
                x_max += pitch - (x_max - ylo) % pitch
                if y > y0:
                    renderer.color = err_lo_color
                else:
                    renderer.color = err_hi_color
                # Loop over hatch lines.
                for x in hep.num.range(x_min, x_max, pitch):
                    # Crop the hatch line to the bin area.
                    d0 = max(0, x0 - x)
                    d1 = max(0, min(y - ylo, x1 - x))
                    if d0 == d1:
                        continue
                    renderer.line(
                        ((x + d0, ylo + d0), (x + d1, ylo + d1)))

        # Draw the outline.
        if line_color:
            # Set up for drawing the outline.
            renderer.color = line_color
            renderer.thickness = thickness
            renderer.dash = dash
            # Draw the line outline_segments.
            for points in outline_segments:
                renderer.line(points)


    def _renderBins_points(self, renderer, y_map, (lo, hi), style, bin_iter):
        color = style.get("color", black)
        cross = style.get("cross", True)
        dash = style.get("dash", None)
        errors = style.get("errors", True)
        log_scale = style.get("y_axis_log_scale")
        marker = style.get("marker", None)
        marker_size = style.get("marker_size", 4 * point)
        thickness = style.get("thickness", default_thickness)
        bin_center = style.get("bin_center", 0.5)

        renderer.color = color

        for (x0, x1), value, error in bin_iter:
            x = x0 + bin_center * (x1 - x0)
            err_lo, err_hi = error
            vlo = value - err_lo
            vhi = value + err_hi

            # Draw a horizontal line for the bin contents, if selected.
            if cross and lo <= value <= hi:
                y = y_map(value)
                points = [ (x0, y), (x1, y) ]
                renderer.thickness = thickness
                renderer.dash = dash
                renderer.line(points)
            # Draw a vertical line for the bin error, if selected.
            if errors and lo < vhi and vlo < hi:
                ylo = y_map(max(lo, vlo))
                yhi = y_map(min(hi, vhi))
                points = [ (x, ylo), (x, yhi) ]
                renderer.thickness = thickness
                renderer.dash = dash
                renderer.line(points)
            # Draw the marker, if selected.
            if marker is not None and lo <= value <= hi:
                y = y_map(value)
                renderer.marker((x, y), marker, marker_size)


    def _render(self, renderer, region, **style):
        from hep.draw import latex
        formatNumber = latex.formatNumber

        histogram = self.histogram
        style.update(self.style)

        # Extract styles.
        bin_style = style.get("bins", "points")
        xlo, xhi = style.get("x_axis_range", histogram.axis.range)
        ylo, yhi = style.get("y_axis_range", getRange(histogram))
        log_scale = style.get("y_axis_log_scale")
        stats = style.get("stats", "")
        stats_position = style.get("stats_position", "right")
        bin_width = self._getNormalBinWidth(style)
        suppress_zero_bins = style.get("suppress_zero_bins", False)

        # Compute coordinates.
        ((x0, y0, x1, y1), 
         (x_overflows, y_overflows),
         (xuf, xof, yuf, yof)) = setupOverflows(region, style)

        # Find the bin renderering function for the bin style.
        render_bins = getattr(self, "_renderBins_%s" % bin_style, None)
        if render_bins is None:
            raise ValueError, "unknown bin style '%s'" % bin_style

        # Build transformations from the plot's coordinate space to
        # physical coordinates in the main data region of the plot.
        x_scale = (x1 - x0) / (xhi - xlo)
        x_map = lambda x: (x - xlo) * x_scale + x0
        if log_scale:
            log_yhi = log10(yhi)
            log_ylo = log10(ylo)
            y_scale = (y1 - y0) / (log_yhi - log_ylo)
            y_map = lambda y: (log10(y) - log_ylo) * y_scale + y0
        else:
            y_scale = (y1 - y0) / (yhi - ylo)
            y_map = lambda y: (y - ylo) * y_scale + y0
        
        # An iterator over bins, returning bin size, contents, and
        # errors. 
        def bin_iter():
            bin_numbers = AxisIterator(
                histogram.axis, False, range=(xlo, xhi))
            for bin_number in bin_numbers:
                x0, x1 = histogram.axis.getBinRange(bin_number)
                if bin_width is None:
                    scale = 1
                else:
                    scale = bin_width / (x1 - x0)
                value = histogram.getBinContent(bin_number)
                if value == 0 and suppress_zero_bins:
                    continue
                err_lo, err_hi = histogram.getBinError(bin_number)
                yield (x_map(x0), x_map(x1)), \
                      value * scale, (err_lo * scale, err_hi * scale)
        # Render the main (i.e. not under/overflow) bins.
        render_bins(renderer, y_map, (ylo, yhi), style, bin_iter())
        
        if x_overflows:
            # Render overflow bins.
            
            # An iterator over just the underflow bin.
            def bin_iter():
                value = histogram.getBinContent("underflow")
                error = histogram.getBinError("underflow")
                yield (xuf[0], xuf[1]), value, error
            # Render the underflow bin.
            render_bins(renderer, y_map, (ylo, yhi), style, bin_iter())

            # An iterator over just the overflow bin.
            def bin_iter():
                value = histogram.getBinContent("overflow")
                error = histogram.getBinError("overflow")
                yield (xof[0], xof[1]), value, error
            # Render the overflow bin.
            render_bins(renderer, y_map, (ylo, yhi), style, bin_iter())



#-----------------------------------------------------------------------

class Histogram2DPlot(Figure):

    def __init__(self, histogram, **style):
        self.histogram = histogram
        Figure.__init__(self, style);
        self.watch_modified.append(histogram)


    def __set_data(self, histogram):
        self.histogram = histogram


    data = property(lambda self: self.histogram, __set_data)


    def getXAxis(self, style):
        return self.histogram.axes[0]


    def getYAxis(self, x_range, style):
        return self.histogram.axes[1]


    def _getNormalBinWidths(self, style):
        """Return the bin widths to use for normalizing bin contents.

        returns -- The two bin widths to use as the denominator for
        plotting bin contents.  If 'None', bin contents should be
        displayed without normalizing to a fixed bin width."""
        
        bin_size = style.get("normalize_bin_size", "auto")
        if bin_size == "auto":
            # Use the size of the first bins.
            x0, x1 = self.histogram.axes[0].getBinRange(0)
            y0, y1 = self.histogram.axes[1].getBinRange(0)
            return x1 - x0, y1 - y0
        elif bin_size is None:
            return None
        else:
            size_x, size_y = bin_size
            return size_x, size_y


    def _renderBins_box(self, renderer, (zlo, zhi), style, bin_iter):
        # Extract styles.
        positive_color = style.get(
            "color", default_positive_color)
        negative_color = style.get(
            "negative_color", default_negative_color)
        overrun_color = style.get(
            "overrun_color", default_overrun_color)
        underrun_color = style.get(
            "underrun_color", default_underrun_color)
        z_log_scale = style.get("z_log_scale", False)

        # Set up transformation for z values.
        if z_log_scale:
            log_zhi = log10(zhi)
            log_zlo = log10(zlo)
            z_map = lambda z: (log10(z) - log_zlo) / (log_zhi - log_zlo)
        elif negative_color is None:
            z_map = lambda z: (z - zlo) / (zhi - zlo)
        else:
            z_scale = 1 / max(abs(zlo), abs(zhi))
            z_map = lambda z: z * z_scale

        # Loop over bins.
        for (x0, y0, x1, y1), value, error in bin_iter:
            # Don't draw nonpositive bins in a log scale.
            if z_log_scale and value <= 0:
                continue
            # Transform bin contents.
            z = z_map(value)
            # Choose the color.
            if z < -1 or (z < 0 and negative_color is None):
                z = -1
                renderer.color = underrun_color
            elif z > 1:
                z = 1
                renderer.color = overrun_color
            elif z < 0 and negative_color is not None:
                renderer.color = negative_color
            else:
                renderer.color = positive_color
            # Compute the box size.  Use the square root of the bin
            # value, so that the box's area represents the bin contents.
            size = sqrt(abs(z)) / 2
            cx = (x0 + x1) / 2
            sx = (x1 - x0) * size
            cy = (y0 + y1) / 2
            sy = (y1 - y0) * size
            # Draw the box.
            drawRectangle(renderer, (cx - sx, cy - sy, cx + sx, cy + sy))
            

    def _renderBins_density(self, renderer, (zlo, zhi), style, bin_iter):
        white = colors["white"]
        # Extract styles.
        positive_color = style.get(
            "color", default_positive_color)
        negative_color = style.get(
            "negative_color", default_negative_color)
        overrun_color = style.get(
            "overrun_color", default_overrun_color)
        underrun_color = style.get(
            "underrun_color", default_underrun_color)
        z_log_scale = style.get("z_log_scale", False)
        
        # Set up transformation for z values.
        if z_log_scale:
            log_zhi = log10(zhi)
            log_zlo = log10(zlo)
            z_map = lambda z: (log10(z) - log_zlo) / (log_zhi - log_zlo)
        elif negative_color is None:
            z_map = lambda z: (z - zlo) / (zhi - zlo)
        else:
            z_scale = 1 / max(abs(zlo), abs(zhi))
            z_map = lambda z: z * z_scale
        # Set up color transformation.
        pos_r = positive_color.red - white.red
        pos_g = positive_color.green - white.green
        pos_b = positive_color.blue - white.blue
        if negative_color is not None:
            neg_r = negative_color.red - white.red
            neg_g = negative_color.green - white.green
            neg_b = negative_color.blue - white.blue

        renderer.thickness = 0.5 * point
        renderer.dash = None
            
        # Loop over bins.
        for (x0, y0, x1, y1), value, error in bin_iter:
            # Don't draw nonpositive bins in a log scale.
            if z_log_scale and value <= 0:
                continue
            # Tranform bin contents.
            z = z_map(value)
            # Compute the box color.
            if z < -1 or (z < 0 and negative_color is None):
                renderer.color = underrun_color
            elif z > 1:
                renderer.color=  overrun_color
            elif z < 0:
                renderer.color = Color(white.red - z * neg_r,
                                       white.green - z * neg_g,
                                       white.blue - z * neg_b)
            else:
                renderer.color = Color(white.red + z * pos_r,
                                       white.green + z * pos_g,
                                       white.blue + z * pos_b)
            # Draw the box.
            renderer.polygon(((x0, y0), (x0, y1), (x1, y1), (x1, y0)))
            # FIXME: Is there a better way to handle this?
            # Draw a thin outline around the box.  This prevents faint
            # "grout lines" from appearing between adjacent boxes.
            renderer.line(((x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)))
            

    def _render(self, renderer, region, **style):
        histogram = self.histogram
        x_axis, y_axis = histogram.axes
        style.update(self.style)

        # Extract styles.
        bin_style = style.get("bins", "density")
        xlo, xhi = style.get("x_axis_range", x_axis.range)
        ylo, yhi = style.get("y_axis_range", y_axis.range)
        z_log_scale = style.get("z_log_scale")
        x_overflows = style.get("x_axis_overflows", True)
        y_overflows = style.get("y_axis_overflows", True)
        suppress_zero_bins = style.get("suppress_zero_bins", False)
        bin_widths = self._getNormalBinWidths(style)
        if bin_widths is None:
            bin_area = None
        else:
            bin_area = bin_widths[0] * bin_widths[1]

        z_range = style.get("z_range", None)
        if z_range is None:
            bin_numbers = hep.hist.AxesIterator(
                histogram.axes, range=((xlo, xhi), (ylo, yhi)),
                overflows=x_overflows or y_overflows)
            z_range = getBinRange(histogram, bin_numbers, False,
                                  z_log_scale, bin_area)
        zlo, zhi = z_range

        # Compute coordinates.
        ((x0, y0, x1, y1), 
         (x_overflows, y_overflows),
         (xuf, xof, yuf, yof)) = setupOverflows(region, style)

        # Find the bin renderering function for the bin style.
        render_bins = getattr(self, "_renderBins_%s" % bin_style, None)
        if render_bins is None:
            raise ValueError, "unknown bin style '%s'" % bin_style

        # Build transformations from the plot's coordinate space to
        # physical coordinates in the main data region of the plot.
        x_scale = (x1 - x0) / (xhi - xlo)
        x_map = lambda x: (x - xlo) * x_scale + x0
        y_scale = (y1 - y0) / (yhi - ylo)
        y_map = lambda y: (y - ylo) * y_scale + y0

        def bin_iter():
            bin_numbers = AxesIterator(
                histogram.axes, True, range=((xlo, xhi), (ylo, yhi)))
            for bin_number in bin_numbers:
                area = 1

                if (not x_overflows) \
                   and bin_number[0] in ("underflow", "overflow"):
                    continue
                if bin_number[0] == "underflow":
                    x0, x1 = xuf
                elif bin_number[0] == "overflow":
                    x0, x1 = xof
                else:
                    bin_x0, bin_x1 = x_axis.getBinRange(bin_number[0])
                    x0 = x_map(bin_x0)
                    x1 = x_map(bin_x1)
                    area *= bin_x1 - bin_x0

                if (not y_overflows) \
                   and bin_number[1] in ("underflow", "overflow"):
                    continue
                if bin_number[1] == "underflow":
                    y0, y1 = yuf
                elif bin_number[1] == "overflow":
                    y0, y1 = yof
                else:
                    bin_y0, bin_y1 = y_axis.getBinRange(bin_number[1])
                    y0 = y_map(bin_y0)
                    y1 = y_map(bin_y1)
                    area *= bin_y1 - bin_y0

                if bin_area is None \
                   or bin_number[0] in ("underflow", "overflow") \
                   or bin_number[1] in ("underflow", "overflow"):
                    scale = 1
                else:
                    scale = bin_area / area

                value = histogram.getBinContent(bin_number)
                if value == 0 and suppress_zero_bins:
                    continue
                err_lo, err_hi = histogram.getBinError(bin_number)
                yield (x0, y0, x1, y1), \
                      value * scale, (err_lo * scale, err_hi * scale)

        # Render the main bins.
        render_bins(renderer, (zlo, zhi), style, bin_iter())



#-----------------------------------------------------------------------

class ScatterPlot(Figure):

    def __init__(self, scatter, **style):
        self.scatter = scatter
        Figure.__init__(self, style)
        self.watch_modified.append(scatter)


    def __set_data(self, scatter):
        self.scatter = scatter


    data = property(lambda self: self.scatter, __set_data)


    def getXAxis(self, style):
        data_range = self.scatter.range
        x_axis = self.scatter.axes[0]
        result = hep.hist.Axis(x_axis.type, range=data_range[0])
        if hasattr(x_axis, "name"):
            result.name = x_axis.name
        if hasattr(x_axis, "units"):
            result.units = x_axis.units
        return result


    def getYAxis(self, x_range, style):
        data_range = self.scatter.range
        y_axis = self.scatter.axes[1]
        result = hep.hist.Axis(y_axis.type, range=data_range[1])
        if hasattr(y_axis, "name"):
            result.name = y_axis.name
        if hasattr(y_axis, "units"):
            result.units = y_axis.units
        return result


    def _render(self, renderer, region, **style):
        scatter = self.scatter
        style = dict(style)
        style.update(self.style)

        # Extract styles.
        data_range = scatter.range
        xlo, xhi = style.get("x_axis_range", data_range[0])
        ylo, yhi = style.get("y_axis_range", data_range[1])
        x_overflows = style.get("x_axis_overflows", True)
        y_overflows = style.get("y_axis_overflows", True)
        color = style.get("color", black)
        marker = style.get("marker", "filled dot")
        marker_size = style.get("marker_size", 2 * point)

        # Compute coordinates.
        ((x0, y0, x1, y1), 
         (x_overflows, y_overflows),
         (xuf, xof, yuf, yof)) = setupOverflows(region, style)
        # Build transformations from the plot's coordinate space to
        # physical coordinates in the main data region of the plot.
        x_scale = (x1 - x0) / (xhi - xlo)
        x_map = lambda x: (x - xlo) * x_scale + x0
        y_scale = (y1 - y0) / (yhi - ylo)
        y_map = lambda y: (y - ylo) * y_scale + y0

        renderer.color = color
        for x, y in scatter.points:
            if x < xlo:
                if x_overflows:
                    x = (xuf[0] + xuf[1]) / 2
                else:
                    continue
            elif x > xhi:
                if x_overflows:
                    x = (xof[0] + xof[1]) / 2
                else:
                    continue
            else:
                x = x_map(x)

            if y < ylo:
                if y_overflows:
                    y = (yuf[0] + yuf[1]) / 2
                else:
                    continue
            elif y > yhi:
                if y_overflows:
                    y = (yof[0] + yof[1]) / 2
                else:
                    continue
            else:
                y = y_map(y)

            renderer.marker((x, y), marker, marker_size)



#-----------------------------------------------------------------------

class Function1DPlot(Figure):

    function = modified.Property("function")


    def __init__(self, function, **style):
        self.function = function
        Figure.__init__(self, style)
        self.watch_modified.append(function)


    def __set_data(self, function):
        self.function = function


    data = property(lambda self: self.function, __set_data)


    def getXAxis(self, style):
        return self.function.axis


    def getYAxis(self, x_range, style):
        """Concoct a y axis object appropriate for the function

        'x_range' -- The range of x values that are being plotted."""

        function = self.function
        style = dict(style)
        style.update(self.style)
        errors        = style.get("errors", False)
        log_scale     = style.get("y_axis_log_scale", False)
        num_samples   = style.get("number_of_samples", 250)

        # Find the range of y values over the specified x range.
        lo, hi = hep.hist.function.getRange(function, x_range, num_samples)
        # Make an unbinned axis with this range.
        y_axis = hep.hist.Axis(function.axis.type, range=(lo, hi))

        # Set the axis label.
        if "y_axis_label" in style:
            y_axis.label = style["y_axis_label"]
        if hasattr(function, "units"):
            y_axis.units = function.units
            
        return y_axis


    def _renderBins_curve(self, renderer, y_map, (lo, hi), style, bin_iter):
        dash          = style.get("dash", None)
        errors        = style.get("errors", False)
        color         = style.get("color", black)
        thickness     = style.get("thickness", 0.75 * point)
        log_scale     = style.get("y_log_scale")

        # Collect line segments for the curve.
        points = []
        segments = []
        # Loop over samples.
        for x, value, (err_lo, err_hi) in bin_iter:
            # If we get a 'None' value, skip it.
            if value is None:
                # Also start a new segment.
                if len(points) > 0:
                    segments.append(points)
                    points = []
                continue
            # Constrain the value to the range of the histogram.
            v = constrain(value, lo, hi)
            y = y_map(v)
            # Include the point.
            points.append((x, y))
        # Include the last segment.
        if len(points) > 0:
            segments.append(points)

        # Draw the curve.
        renderer.color = color
        renderer.dash = dash
        renderer.thickness = thickness
        for segment in segments:
            renderer.line(segment)


    def _render(self, renderer, region, **style):
        function = self.function
        if function is None:
            return

        style.update(self.style)

        # Extract styles.
        bin_style     = style.get("bins", "curve")
        num_samples   = style.get("number_of_samples", 250)
        log_scale     = style.get("y_axis_log_scale")

        # Determine the x range.
        default_x_axis_range = (0, 1)
        if hasattr(function.axis, "range"):
            default_x_axis_range = function.axis.range
        xlo, xhi = style.get("x_axis_range", default_x_axis_range)
        # Determine the y range.
        default_y_axis_range = hep.hist.function.getRange(
            function, (xlo, xhi), num_samples)
        ylo, yhi = style.get("y_axis_range", default_y_axis_range)

        # Compute coordinates.
        ((x0, y0, x1, y1), 
         (x_overflows, y_overflows),
         (xuf, xof, yuf, yof)) = setupOverflows(region, style)

        # Find the bin renderering function for the bin style.
        render_bins = getattr(self, "_renderBins_%s" % bin_style, None)
        if render_bins is None:
            raise ValueError, "unknown bin style '%s'" % bin_style

        # Build transformations from the plot's coordinate space to
        # physical coordinates in the main data region of the plot.
        x_scale = (x1 - x0) / (xhi - xlo)
        x_map = lambda x: (x - xlo) * x_scale + x0
        if log_scale:
            log_yhi = log10(yhi)
            log_ylo = log10(ylo)
            y_scale = (y1 - y0) / (log_yhi - log_ylo)
            y_map = lambda y: (log10(y) - log_ylo) * y_scale + y0
        else:
            y_scale = (y1 - y0) / (yhi - ylo)
            y_map = lambda y: (y - ylo) * y_scale + y0
        
        # An iterator over bins, returning sample position, value, and
        # errors. 
        def bin_iter():
            # Scan over evenly-spaced points.
            delta = (xhi - xlo) / (num_samples - 1)
            for x in hep.num.range(xlo, xhi + 1e-18, delta):
                # Compute the function value.
                y = function(x)
                # No errors for now.
                yield x_map(x), y, (None, None)

        # Render the main (i.e. not under/overflow) bins.
        render_bins(renderer, y_map, (ylo, yhi), style, bin_iter())
        


#-----------------------------------------------------------------------

class Graph(Figure):

    def __init__(self, graph, **style):
        self.graph = graph
        Figure.__init__(self, style)
        self.watch_modified.append(graph)


    def __set_data(self, graph):
        self.graph = graph


    data = property(lambda self: self.graph, __set_data)


    def getXAxis(self, style):
        return self.graph.axes[0]


    def getYAxis(self, x_range, style):
        return self.graph.axes[1]


    def _render(self, renderer, region, **style):
        graph = self.graph
        if graph is None:
            return

        style.update(self.style)

        color         = style.get("line_color", black)
        dash          = style.get("dash", None)
        thickness     = style.get("thickness", default_thickness)
        xlo, xhi      = style.get("x_axis_range", graph.axes[0].range)
        ylo, yhi      = style.get("y_axis_range", graph.axes[1].range)
        
        # Compute coordinates.
        ((x0, y0, x1, y1), 
         (x_overflows, y_overflows),
         (xuf, xof, yuf, yof)) = setupOverflows(region, style)
        # Build transformations from the plot's coordinate space to
        # physical coordinates in the main data region of the plot.
        x_scale = (x1 - x0) / (xhi - xlo)
        x_map = lambda x: (x - xlo) * x_scale + x0
        y_scale = (y1 - y0) / (yhi - ylo)
        y_map = lambda y: (y - ylo) * y_scale + y0

        renderer.color = color
        renderer.dash = dash
        renderer.thickness = thickness
        for sx0, sy0, sx1, sy1 in graph.segments:
            renderer.line(((x_map(sx0), y_map(sy0)),
                           (x_map(sx1), y_map(sy1))))



#-----------------------------------------------------------------------

class Annotation(Figure):
    """Text annotations in the plot area.

    Annotations consists of lines of text that are drawn in the
    upper-left or upper-right corner of the data area of a plot.

    The following styles are used:

    'annotation_position' -- The position of the annotations,
    either'"left"' or '"right"'.

    'annotation_font', 'annotation_font_size', 'annotation_leading',
    'annotation_color' -- Visual style of leading text.
    """

    def __init__(self, text=None, **style):
        """Create annotations consisting of text."""

        self.lines = []
        if text is not None:
            self.append(text)
        Figure.__init__(self, style)


    def append(self, text):
        """Append one or more lines of text.

        'text' -- Text to add.  If it contains linefeeds, it is broken
        into multiple lines."""

        # Split 'text' into lines.
        lines = [ l.strip() for l in text.strip().split("\n") ]
        for line in lines:
            self.lines.append(line.strip())


    def __lshift__(self, text):
        """Synonym for 'append'."""

        self.append(text)


    def _render(self, renderer, region, **style):
        x0, y0, x1, y1 = region

        style.update(self.style)
        position = style.get("annotation_position", "right")
        if position == "left":
            x = x0
            alignment = (0, 0)
        elif position == "right":
            x = x1
            alignment = (1, 0)
        else:
            raise ValueError, \
                  "unknown annotation position %r" % position

        # Construct the text style for rendering annotation lines.
        text_style = dict(style)
        getStyle = \
            lambda n, d: style.get("annotation_" + n, style.get(n, d))
        text_style["font"]          = getStyle("font", "Times")
        text_style["font_size"]     = getStyle("font_size", 8 * point)
        text_style["color"]         = getStyle("color", black)

        leading = style.get(
            "annotation_leading", text_style["font_size"])

        y = y1
        for line in self.lines:
            latex.render(renderer, (x, y), line, text_style, alignment)
            y -= leading



#-----------------------------------------------------------------------

class Statistics(Annotation):
    """Annotation of histograms' statistics.

    An annotation displaying statistics of one or more histograms.  See
    styles for class 'Annotation' for style options."""
    

    def __init__(self, statistics, *histograms, **style):
        """Create annotation of statistics of 'histograms'."""
        
        Annotation.__init__(self, **style)

        # Split the specified statistics.
        self.statistics = tuple(statistics)
        self.histograms = histograms


    def _render(self, renderer, region, **style):
        # Regenerate annotation lines before calling the base class
        # rendering method.
        self.lines = []
        for h, histogram in enumerate(self.histograms):
            # If we're showing statistics for more than one histogram,
            # show the histogram title.
            if len(self.histograms) > 1:
                # First a blank line if this isn't the first one.
                if h > 0:
                    self << ""
                if hasattr(histogram, "title"):
                    title = histogram.title
                elif hasattr(histogram, "name"):
                    title = histogram.name
                elif histogram.dimensions == 1 \
                     and hasattr(histogram.axis, "name"):
                    title = histogram.axis.name
                else:
                    title = "histogram %d" % h
                self << title + " :"
            self << formatStatistics(self.statistics, histogram)

        # Now render.
        Annotation._render(self, renderer, region, **style)

        

#-----------------------------------------------------------------------

class Plot(Figure):

    def __init__(self, dimensions, *objects, **style):
        """Create a plot object.

        'dimensions' -- The number of independent variables in the
        plot.  May be either '1' or '2'.

        '*object' -- Objects to append to the plot.  See 'append'.

        '**style' -- Additional style attributes for the plot."""

        if dimensions not in (1, 2):
            raise ValueError, "invalid dimensions %s" % dimensions

        self.series = modified.List()
        self.dimensions = dimensions

        self.x_axis = Axis(None, "x")
        self.y_axis = Axis(None, "y")
        self.background = Canvas((0, 0, 1, 1), border=0, aspect=None)
        self.annotations = Canvas((0, 0, 1, 1), border=0, aspect=None)

        for object in objects:
            self.append(object)

        Figure.__init__(self, style)
        self.watch_modified.append(self.series)
        self.watch_modified.append(self.x_axis)
        self.watch_modified.append(self.y_axis)
        self.watch_modified.append(self.background)
        self.watch_modified.append(self.annotations)


    def append(self, object, **style):
        """Add a series to plot 'object'.

        Appends to 'series' a plot object suitable for plotting
        'object'.

        'object' -- The object to plot.  May be a 1-D or 2-D histogram
        or scatter.  If it is a 'Figure', it is simply appended to the
        list of 'series'.

        '**style' -- Additional style attributes for plotting 'object'.
        """

        if isinstance(object, Figure):
            self.series.append(object)

        elif isHistogram(object):
            if object.dimensions != self.dimensions:
                raise ValueError, \
                      "can't plot %d-D histogram in %d-D plot" \
                      % (object.dimensions, self.dimensions)
            if object.dimensions == 1:
                plot_series = Histogram1DPlot(object, **style)
                self.series.append(plot_series)
            elif object.dimensions == 2:
                plot_series = Histogram2DPlot(object, **style)
                self.series.append(plot_series)
            else:
                raise ValueError, \
                      "don't know how to plot %d-D histogram" \
                      % object.dimensions
        
        elif isScatter(object):
            if self.dimensions != 2:
                raise ValueError, \
                      "can't plot a scatter in a %d-D plot" \
                      % self.dimensions
            self.series.append(ScatterPlot(object, **style))

        elif isFunction(object):
            if self.dimensions == 1:
                self.series.append(Function1DPlot(object, **style))
            else:
                raise ValueError, \
                      "don't know hot to plot %d-D function" \
                      % object.dimensions

        elif isGraph(object):
            if self.dimensions != 2:
                raise ValueError, \
                      "can't plot a graph in a %d-D plot" \
                      % self.dimensions
            self.series.append(Graph(object, **style))
        else:
            raise TypeError, "don't know how to plot %r" % (object, )



    def _getNormalBinSize(self, x_axes, y_axes):
        # Take the bin size from the first bin of the first series with
        # binned axes.
        if self.dimensions == 1:
            for x_axis in x_axes:
                if isinstance(x_axis, BinnedAxis):
                    x0, x1 = x_axis.getBinRange(0)
                    return x1 - x0
        elif self.dimensions == 2:
            for x_axis, y_axis in zip(x_axes, y_axes):
                if isinstance(x_axis, BinnedAxis) \
                   and isinstance(y_axis, BinnedAxis):
                    x0, x1 = x_axis.getBinRange(0)
                    y0, y1 = y_axis.getBinRange(0)
                    return x1 - x0, y1 - y0
        else:
            raise NotImplementedError


    def _render(self, renderer, region):
        # Select series that contain data.
        series = [ s for s in self.series
                   if not hasattr(s, "data") or s.data is not None ]

        # Scale some styles to a size appropriate for the overall size
        # of the plot.
        scale = min(region[2] - region[0], region[3] - region[1])
        font_size = max(6, min(16, 30 * scale + 6)) * point
        marker_size = max(2, min(6, 5 * scale)) * point
        thickness = max(0.25, min(1, 8 * scale)) * point

        # Constuct the style.
        style = dict(self.style)
        sg = style.get
        ss = style.__setitem__
        sd = style.setdefault

        # Get some major styles, which influence other defaults.
        overflows       = sg("overflows", True)
        log_scale       = sg("log_scale", False)

        # Set some axis styles, which depend on the number of
        # dimensions.
        if self.dimensions == 1:
            ss(              "x_axis_overflows",    overflows)
            ss(              "y_axis_overflows",    False)
            ss(              "x_axis_log_scale",    False)
            ss(              "y_axis_log_scale",    log_scale)
        elif self.dimensions == 2:
            ss(              "x_axis_overflows",    overflows)
            ss(              "y_axis_overflows",    overflows)
            ss(              "x_axis_log_scale",    False)
            ss(              "y_axis_log_scale",    False)
            ss(              "z_axis_log_scale",    log_scale)

        # Set these defaults in the style, so that subobjects get the
        # same defaults.
        color           = sd("color",               black)
        errors          = sd("errors",              True)
        font            = sd("font" ,               "Times")
        font_size       = sd("font_size",           font_size)
        marker_size     = sd("marker_size",         marker_size)
        thickness       = sd("thickness",           thickness)
        x_axis_position = sd("x_axis_position",     "bottom")
        y_axis_position = sd("y_axis_position",     "left")
        
        # Some default styles depend on the number of dimensions.
        if self.dimensions == 1:
            unused      = sd("min_aspect",          1.5) 
            zline       = sd("zero_line",           True)
        elif self.dimensions == 2:
            unused      = sd("aspect",              1)
            zline       = sd("zero_line",           False)

        # Get any other styles we need.
        bin_size        = sg("normalize_bin_size",  "auto")
        bottom_margin   = sg("bottom_margin",       0.012)
        caption         = sg("caption",             None)
        left_margin     = sg("left_margin",         0.015)
        oline           = sg("overflow_line",       True)
        oline_color     = sg("overflow_line_color", black)
        oline_dash      = sg("overflow_line_dash",  (0.0002, 0.0002))
        oline_thickness = sg("overflow_line_thickness", 0.1 * point)
        right_margin    = sg("right_margin",        0.005)
        show_layout     = sg("show_layout",         False)
        title           = sg("title",               None)
        top_margin      = sg("top_margin",          0.008)
        x_axis_log_scale= sg("x_axis_log_scale")
        y_axis_log_scale= sg("y_axis_log_scale")
        zline_color     = sg("zero_line_color",     black)
        zline_dash      = sg("zero_line_dash",      None)
        zline_thickness = sg("zero_line_thickness", 0.5 * point)

        # Combine x axes for all the series together.
        x_axes = [ s.getXAxis(style)
                   for s in series
                   if hasattr(s, "getXAxis") ]
        x_axis = hep.hist.combineAxisList(x_axes)
        # Find the x axis range.
        xlo, xhi = getRangeForStyle(
            self.style, "x_axis_range", x_axis, x_axis_log_scale)

        # Combine y axes for all the series together.
        y_axes = [ s.getYAxis((xlo, xhi), style) 
                   for s in series
                   if hasattr(s, "getYAxis") ]
        y_axis = hep.hist.combineAxisList(y_axes)
        # Find the y axis range.
        ylo, yhi = getRangeForStyle(
            style, "y_axis_range", y_axis, y_axis_log_scale)
        
        # Store the axis ranges.
        ss(                  "x_axis_range",        (xlo, xhi))
        ss(                  "y_axis_range",        (ylo, yhi))

        # If requested, choose a normal bin size automatically.
        if bin_size == "auto":
            bin_size = self._getNormalBinSize(x_axes, y_axes)
        ss(                  "normalize_bin_size",  bin_size)

        region = adjustRegionForStyle(region, style)

        # Divide the real estate among the axes and the data proper.
        x0, y0, x1, y1 = region
        data_x0 = x0 + left_margin
        data_x1 = x1 - right_margin
        data_y0 = y0 + bottom_margin
        data_y1 = y1 - top_margin
        # Place the vertical axis.
        if y_axis_position == "left":
            y_axis_x0 = x0
            y_axis_x1 = data_x0
        elif y_axis_position == "right":
            y_axis_x0 = data_x1
            y_axis_x1 = x1
        # Place the horizontal axis.
        if x_axis_position == "bottom":
            x_axis_y0 = y0
            x_axis_y1 = data_y0
        elif x_axis_position == "top":
            x_axis_y0 = data_y1
            x_axis_y1 = y1
            
        # Draw dotted lines depicting the layout; primarily for
        # debugging.
        if show_layout:
            renderer.color = black
            renderer.dash = (0.001, 0.001)
            renderer.thickness = 0.2 * point
            drawFrame(renderer, region)
            drawFrame(renderer, (data_x0, data_y0, data_x1, data_y1))

        # Compute coordinates for overflows.
        ((dx0, dy0, dx1, dy1), 
         (x_overflows, y_overflows),
         (xuf, xof, yuf, yof)) = setupOverflows(
            (data_x0, data_y0, data_x1, data_y1), style)

        # Render the background.
        self.background.region = (xlo, ylo, xhi, yhi)
        self.background._render(renderer, (dx0, dy0, dx1, dy1))

        # Render the x axis.
        if x_axis_position is not None:
            # Use the x axis we negotiated with the data series.
            self.x_axis.axis = x_axis
            # Render it
            self.x_axis._render(
                renderer, (data_x0, x_axis_y0, data_x1, x_axis_y1),
                range=(xlo, xhi), **style)

        # Render the y axis.
        if y_axis_position is not None:
            # Use the y axis we negotiated with the data series.
            self.y_axis.axis = y_axis
            # Render it.
            self.y_axis._render(
                renderer, (y_axis_x0, data_y0, y_axis_x1, data_y1),
                range=(ylo, yhi), **style)
        
        # Draw light vertical lines separating the underflow and
        # overflow areas from the main plot.
        if oline:
            renderer.color = oline_color
            renderer.dash = oline_dash
            renderer.thickness = oline_thickness
            if x_overflows:
                x = (xuf[1] + dx0) / 2
                renderer.line(((x, data_y0), (x, data_y1)))
                x = (dx1 + xof[0]) / 2
                renderer.line(((x, data_y0), (x, data_y1)))
            if self.dimensions == 2 and y_overflows:
                y = (yuf[1] + dy0) / 2
                renderer.line(((data_x0, y), (data_x1, y)))
                y = (dy1 + yof[0]) / 2
                renderer.line(((data_x0, y), (data_x1, y)))

        # Render a zero line.
        if zline and ylo <= 0 <= yhi:
            y = data_y0 + (data_y1 - data_y0) * -ylo / (yhi - ylo)
            renderer.color = zline_color
            renderer.thickness = zline_thickness
            renderer.dash = zline_dash
            renderer.line(((dx0, y), (dx1, y)))
            if x_overflows:
                xuf0, xuf1 = xuf
                renderer.line(((xuf0, y), (xuf1, y)))
                xof0, xof1 = xof
                renderer.line(((xof0, y), (xof1, y)))

        # Render data series.
        for s in series:
            s._render(
                renderer, (data_x0, data_y0, data_x1, data_y1),
                **style)

        # Render the annotations.
        self.annotations.region = (xlo, ylo, xhi, yhi)
        self.annotations._render(renderer, (dx0, dy0, dx1, dy1))

        # Render the title and caption.
        renderer.color = color
        renderer.font = (font, font_size)
        if title is not None:
            renderLatex(renderer, (data_x1, y1), title, style,
                        alignment=(1, 1.2))
        if caption is not None:
            renderLatex(renderer, (x0, y0), caption, style,
                        alignment=(0, 0))


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def makeNiceRange(range, include_zero=True, log_scale=False):
    """Heuristically expand 'range' to a range of "round" numbers.

    'range' -- A '(lo, hi)' pair.

    'include_zero' -- If true, require that zero is an element of the
    range.

    'log_scale' -- If true, assume 'range' will be interpreted on a log
    scale.  May not be specified when 'include_zero' is true.

    returns -- An expanded '(lo, hi)' pair."""

    assert not include_zero or not log_scale

    lo, hi = range

    if include_zero:
        if lo < 0 and hi < 0:
            hi = 0
        if lo > 0 and hi > 0:
            lo = 0
            
    if log_scale:
        # Round each to the nearest power of ten.
        lo_scale = 10 ** floor(log10(lo))
        lo -= lo % lo_scale
        hi_scale = 10 ** floor(log10(hi))
        hi += hi_scale - hi % hi_scale
    else:
        if lo == 0 and hi == 0:
            lo, hi = 0, 1
        # Figure out the order of magnitude of the values.
        scale = 10 ** int(log10(max(abs(lo), abs(hi))) - 1.5)
        # Round each to the nearest multiple of the scale.
        lo -= lo % scale
        if hi % scale != 0:
            hi = hi + scale - hi % scale

    return lo, hi


def getRangeForStyle(style, key, axis, log_scale=False):
    # Determine the range according to the axis.
    if axis is not None and hasattr(axis, "range"):
        axis_range = axis.range
    else:
        # No range to be had.
        axis_range = (0, 1)

    if key in style:
        # The range was specified in the style.
        try:
            lo, hi = style[key]
        except (TypeError, ValueError):
            raise ValueError, "range must be a two-element sequence"

        # If either of the range limits are 'None', use the
        # automatically-determined values.
        if lo is None:
            lo = axis_range[0]
        if hi is None:
            hi = axis_range[1]

        if isinstance(axis, BinnedAxis):
            # Adjust the low range to the next higher bin edge, and the
            # high range to the next lower bin edge.
            new_lo = None
            new_hi = None
            for bin_number in AxisIterator(axis):
                bin_lo, bin_hi = axis.getBinRange(bin_number)
                if new_lo is None or bin_lo > lo:
                    new_lo = lo
                if new_hi is None or bin_hi < hi:
                    new_hi = hi
            lo = new_lo
            hi = new_hi

    else:
        # No range was specified in the style.  Take it from the axis.
        lo, hi = axis_range

    # Make sure they're ordered correctly.
    if lo > hi:
        lo, hi = hi, lo

    if log_scale:
        if hi <= 0:
            # The entire range is negative!  Oh well.
            lo = 0.1
            hi = 1
        elif lo <= 0:
            lo = min(0.1, 0.1 * hi)
            
    # Slightly expand the range to account for roundoff errors.
    elif type(lo) == float:
        lo -= abs(lo) * 1e-8
        hi += abs(hi) * 1e-8

    return lo, hi


def chooseTicksForBinnedAxis(axis, rrange, num_ticks):
    """Choose positions of tick marks for an axis.

    'axis' -- The axis for which ticks are chosen.

    'num_ticks' -- The approximate number of tick marks to use.

    returns -- A sequence of positions along the axis at which to draw
    tick marks."""

    # Evenly place the ticks along the range.
    lo, hi = rrange
    delta = (hi - lo) / (num_ticks - 1)
    ticks = tuple(hep.num.range(lo, hi + delta / 2, delta))

    # Now scan over the ticks, moving each one to the nearest bin edge,
    # unless it is outside of the axis range.
    aligned_ticks = []
    axis_lo, axis_hi = axis.range
    for tick in ticks:
        # Only align ticks that are in the axis range.
        if axis_lo <= tick < axis_hi:
            # Find the bin containing the tick position.
            bin_number = axis(tick)
            # Place the tick at the nearer edge.
            bottom, top = axis.getBinRange(bin_number)
            if tick - bottom < top - tick:
                tick = bottom
            else:
                tick = top
        aligned_ticks.append(tick)

    # Remove duplicates.
    aligned_ticks = hep.fn.unique(aligned_ticks)

    return aligned_ticks



def chooseTicksForRange(range, axis_type, num_ticks, show_min_max):
    """Choose tick positions for 'range'.

    'range' -- The '(lo, hi)' range of values shown on the axis.

    'axis_type' -- The Python type of the values on the axis.

    'num_ticks' -- The approximate desired number of ticks.

    'show_min_max' -- If true, force 'lo' and 'hi' as the smallest and
    largest tick positions.

    returns -- A sequence of tick positions."""

    min, max = range
    if axis_type is None:
        axis_type = type(coerce(min, max)[0])

    # Compute the power-of-ten scale of the axis range.
    if max == min:
        if max == 0:
            scale = 1.
        else:
            scale = math.log10(abs(max))
    else:
        scale = math.log10(abs(max - min))
    # Don't use a fractional scale for non-floating point values.
    if scale < 1 and axis_type is not float:
        scale = 1
    # Choose a division that is a power of ten and that will give us
    # in the ballpark of ten ticks. 
    division = 10 ** (round(scale) - 1)
    count = (max - min) / division
    # Tune the division to get a nice number of ticks with a division
    # that is a multiple of 2, 2.5, 5, or 10.
    if count < (num_ticks / 3):
        division /= 4
    elif count < (num_ticks / 1.5):
        division /= 2
    elif count > (num_ticks * 8):
        division *= 10
    elif count > (num_ticks * 4):
        division *= 5
    elif count > (num_ticks * 1.5):
        division *= 2

    # Now scan over the range of the axis, assigning tick marks.  
    if show_min_max:
        # Start with the minimum value, even if it's not a multiple of
        # the division.
        ticks = [ min ]
        # The first tick position is the next multiple of the division.
        x = math.ceil(min / division) * division
        # Suppress it if it is too close to the minimum value.
        if x - min < division / 5:
            x += division
    else:
        # The first tick position is the first multiple of the division.
        x = math.ceil(min / division) * division
        ticks = []
    # Place ticks at consecutive multiples of the division, but not past
    # the maximum value.
    while x <= max:
        ticks.append(axis_type(x))
        x += division
    if show_min_max:
        # We also want to use the maximum value, even if it's not a
        # multiple of the division.  If the last round multiple is too
        # close, replace it; otherwise, use the maximum in addition.
        if max - ticks[-1] < division / 4:
            ticks[-1] = max
        else:
            ticks.append(max)

    # Remove duplicates.
    ticks = hep.fn.unique(ticks)

    return map(axis_type, ticks)


def chooseTicksForLogRange(range, axis_type, num_ticks):
    """Choose tick positions for 'range' displayed on a log scale.

    'range' -- The '(lo, hi)' range of values shown on the axis.

    'axis_type' -- The Python type of the values on the axis.

    'num_ticks' -- The approximate desired number of ticks.

    returns -- A sequence of tick positions."""

    lo, hi = range
    if lo <= 0 or hi <= 0:
        raise ValueError, "range must be positive"
    lo_scale = int(floor(log10(lo)))
    hi_scale = int(floor(log10(hi)))
    num_scale = log10(hi) - log10(lo)

    def makeTicks(multiples):
        ticks = []
        for scale in xrange(lo_scale, hi_scale + 1):
            for multiple in multiples:
                ticks.append(multiple * 10 ** scale)
        return ticks

    if num_scale * 8 < num_ticks:
        ticks = makeTicks((1, 2, 3, 4, 5, 6, 7, 8, 9))
    elif num_scale * 4 < num_ticks:
        ticks = makeTicks((1, 2, 4, 6, 8))
    elif num_scale * 1.4 < num_ticks:
        ticks = makeTicks((1, 5))
    else:
        ticks = makeTicks((1, ))

    ticks = filter(lambda t: lo < t < hi, ticks)
    return ticks


def chooseTicks(axis, range, num_ticks, log_scale):
    """Choose tick positions along 'axis'.

    'axis' -- An axis object.

    'range' -- The '(lo, hi)' range of values along 'axis' that are
    dispalyed.

    'ticks' -- The approximate target number of ticks.

    'log_scale' -- If true, choose ticks appropriate for displaying
    'axis' with a log scale.

    returns -- A sequence of tick positions."""

    # Handle binned axes specially.
    if isinstance(axis, EvenlyBinnedAxis):
        return chooseTicksForBinnedAxis(axis, range, num_ticks)
    # Handle linear and log scales differently.
    if log_scale:
        return chooseTicksForLogRange(range, axis.type, num_ticks)
    else:
        return chooseTicksForRange(range, axis.type, num_ticks, False)


def tickLabelFormatter(ticks, style):
    """Return a formatting function for labelling tick positions."""
    
    from hep.draw.latex import scientificNotation

    # Compute the absolute size of the largest tick.
    largest = max(map(abs, ticks))
    if largest == 0:
        # All zero.
        return lambda v: "none"

    # Find the scale factor.
    range = max(ticks) - min(ticks)
    scale = min(largest, range)
    if scale == 0:
        scale = 1
    else:
        scale = log10(scale)
    if scale > 5:
        # Format using scientific notation.
        return lambda v: "$" + scientificNotation(v, 2) + "$"
    elif scale > 2:
        # Format as an integer.
        return lambda v: "%d" % v
    elif scale > -3:
        # Format as a floating-point number.
        return lambda v: "%.*f" % (int(2.5 - scale), v)
    else:
        # Format using scientific notation.
        return lambda v: "$" + scientificNotation(v, 2) + "$"


def setupOverflows(region, style):
    """Compute geometry for displaying overflow bins.

    'region' -- The region for display the histogram data.

    'style' -- The style dictinary.

    returns -- 'region, overflows, overflow_intervals' where 'region' is
    the region for the non-overflow data; 'overflows' is a pair of
    booleans specifying whether to draw x- and y-axis overflows; and
    'overflow_intervals' consists of four pairs specifying the lower and
    upper coordinates of the x underflow, x overflow, y underflow, and y
    overflow bands."""

    # Extract the overall region.
    x0, y0, x1, y1 = region

    # By default, scale the overflow regions to the overall size.
    default_x_size = 0.035 * (x1 - x0)
    default_y_size = 0.035 * (y1 - y0)

    # Exctract style information.
    x_overflows = style.get("x_axis_overflows", True)
    y_overflows = style.get("y_axis_overflows", True)
    x_overflow_size = style.get("overflow_size", default_x_size)
    y_overflow_size = style.get("overflow_size", default_y_size)
    x_overflow_margin = style.get("overflow_margin", default_x_size)
    y_overflow_margin = style.get("overflow_margin", default_y_size)
    
    if x_overflows:
        # Adjust x coordinates for drawing overflows.
        xuf = (x0, x0 + x_overflow_size)
        x0 += x_overflow_size + x_overflow_margin
        xof = (x1 - x_overflow_size, x1)
        x1 -= x_overflow_size + x_overflow_margin
    else:
        xuf = None
        xof = None

    if y_overflows:
        # Adjust y coordinates for drawing overflows.
        yuf = (y0, y0 + y_overflow_size)
        y0 += y_overflow_size + y_overflow_margin
        yof = (y1 - y_overflow_size, y1)
        y1 -= y_overflow_size + y_overflow_margin
    else:
        yuf = None
        yof = None

    # Construct output.
    return (x0, y0, x1, y1), \
           (x_overflows, y_overflows), \
           (xuf, xof, yuf, yof)


def makeAxisLabel(axis):
    if hasattr(axis, "label"):
        return axis.label
    if hasattr(axis, "name"):
        label = axis.name
        if hasattr(axis, "units") and axis.units:
            label += " (%s)" % axis.units
        return label
    if hasattr(axis, "units"):
        return axis.units
    return None


def logScale(value):
    if value > 0:
        return log10(value)
    else:
        return -1e+100


def getBinSize(axes, bin_numbers):
    """Return the total volume of an N-dimensional bin.

    'axes' -- A sequence of axes representing the bin dimensions.

    'bin_numbers' -- A sequence of bin numbers along successive
    dimensions.

    returns -- The N-dimensional volume of the bin."""

    size = 1
    for axis, bin_number in zip(axes, bin_numbers):
        if bin_number in ("underflow", "overflow"):
            continue
        x0, x1 = axis.getBinRange(bin_number)
        size *= x1 - x0
    return size


def getBinRange(histogram, bin_numbers=None, errors=True,
                log_scale=False, bin_area=None):
    """Compute range of bin values of 'histogram'.

    'bin_numbers' -- A sequence of bin numbers over which to compute the
    bin range.

    'errors' -- Whether to include error bars.

    'log_scale' -- Wehther to compute the range assuming a log scale.

    'bin_area' -- The standard bin volume.  If not 'None', bin values
    are normalized to this volume.

    returns -- The '(lo, hi)' range of bin values."""

    if bin_numbers is None:
        bin_numbers = AxesIterator(histogram.axes)

    lo = None
    hi = None
    for bin_number in bin_numbers:
        value = histogram.getBinContent(bin_number)
        err_lo, err_hi = histogram.getBinError(bin_number)
        if errors:
            vlo = value - err_lo
            vhi = value + err_hi
        else:
            vlo = value
            vhi = value
        # Normalize to the bin area.
        if bin_area is not None:
            bin_size = getBinSize(histogram.axes, bin_number)
            scale = bin_area / bin_size
            vlo *= scale
            vhi *= scale
        # Update the maximum and minimum.  If this is a log scale, skip
        # non-positive values.
        if (not log_scale or vlo > 0) \
           and (lo is None or vlo < lo):
            lo = vlo
        if (not log_scale or vhi > 0) \
           and (hi is None or vhi > hi):
            hi = vhi
    # If we didn't get any values, choose something arbitrary.
    if hi is None:
        hi = 1
    if lo is None:
        if log_scale:
            lo = hi / 10
        else:
            lo = 0
    # Go for nice round numbers.
    lo, hi = makeNiceRange(
        (lo, hi), include_zero=not log_scale, log_scale=log_scale)
    # All done.
    return lo, hi


def renderLatex(renderer, position, text, style, alignment):
    """Render LaTeX text.

    If a parse error occurs, handle it but print a warning."""

    try:
        latex.render(renderer, position, text, style, alignment)
    except latex.ParseError:
        print >> sys.stderr, \
              "WARNING: error rendering LaTeX text \"%s\"" % text
        pass
    

def formatStatistics(statistics, histogram):
    """Format 'statistics' of 'histogram' as multi-line text.

    'statistics' -- A sequence of statistics to display.  Each element
    may be one of '"sum"', '"mean"', '"variance"', '"rms"', or
    '"overflows"'.

    returns -- Formatted statistics for 'histogram' as LaTeX text, each
    on a separate line."""
        
    text = ""
    for stat in statistics:
        if stat == "sum":
            text += "sum$=%s$\n" \
                 % formatNumber(integrate(histogram))
        elif stat == "mean":
            text += "mean$=%s$\n" \
                 % formatNumber(mean(histogram)[0])
        elif stat == "variance":
            text += "var$=%s$\n" \
                 % formatNumber(variance(histogram)[0])
        elif stat == "rms":
            text += "RMS$=%s$\n" \
                 % formatNumber(standardDeviation(histogram)[0])
        elif stat == "overflows":
            text += "UF$=%s$\n" \
                 % formatNumber(histogram.getBinContent("underflow"))
            text += "OF$=%s$\n" \
                 % formatNumber(histogram.getBinContent("overflow"))
        elif stat == "max":
            text += "max$=%s$\n" \
                 % formatNumber(getRange(histogram)[1])
        elif stat == "min":
            text += "min$=%s$\n" \
                 % formatNumber(getRange(histogram)[0])
        else:
            raise ValueError, "unknown statistic %r" % stat
    return text


def setSeriesData(plot, *data_items):
    """Set the series data in 'plot' to '*data_items'.

    Sets the histogram, scatter, or function displayed in successive
    series of 'plot' to the corresponding '*data_items'."""

    for series, data in zip(plot.series, data_items):
        series.data = data


#-----------------------------------------------------------------------

def _seriesToDom(series, document):
    series_node = document.createElement("series")
    series_node.setAttribute("type", type(series).__name__)
    series_node.appendChild(_styleToDom(series.style, document))
    return series_node


def _styleToDom(style, document):
    style_node = document.createElement("style")
    for key, value in style.items():
        item_node = document.createElement("attribute")
        item_node.setAttribute("name", key)
        value_node = document.createTextNode(repr(value))
        item_node.appendChild(value_node)
        style_node.appendChild(item_node)
    return style_node


def _plotSchemaToDom(plot, document):
    plot_node = document.createElement("plot-schema")
    plot_node.setAttribute("dimensions", str(plot.dimensions))
    plot_node.appendChild(_styleToDom(plot.style, document))
    for series in plot.series:
        plot_node.appendChild(_seriesToDom(series, document))
    # FIXME: Include annotations.
    return plot_node


def savePlotSchema(plot, path):
    """Save 'plot' as a plot schema in XML file at 'path'.

    A plot schema contains the style and series information of the plot,
    but without the actual histogram, scatter plot, or function data
    displayed in the plot."""
    
    document = makeDomDocument()
    document.appendChild(_plotSchemaToDom(plot, document))
    file(path, "w").write(document.toprettyxml(" "))


def _styleFromDom(node):
    assert node.nodeName == "style"
    style = {}
    for attribute_node in node.childNodes:
        if attribute_node.nodeName != "attribute":
            raise ParseError, "unknown element %r in style" \
                  % attribute_node.nodeName
        name = attribute_node.getAttribute("name")
        value = parseTextElement(attribute_node)[1]
        style[str(name)] = eval(value)
    return style


def _styleForDom(node):
    style_nodes = [ c for c in node.childNodes if c.nodeName == "style" ]
    if len(style_nodes) == 0:
        return {}
    elif len(style_nodes) > 1:
        raise ParseError, "multiple style elements found"
    else:
        return _styleFromDom(style_nodes[0])
                      

def _seriesFromDom(node):
    assert node.nodeName == "series"
    type_name = node.getAttribute("type")
    type_class = globals()[type_name]
    style = _styleForDom(node)
    return type_class(None, **style)


def _plotSchemaFromDom(node):
    assert node.nodeName == "plot-schema"
    dimensions = int(node.getAttribute("dimensions"))
    style = _styleForDom(node)
    plot = Plot(dimensions, **style)
    map(plot.series.append,
        [ _seriesFromDom(c)
          for c in node.childNodes
          if c.nodeName == "series" ])
    return plot


def loadPlotSchema(path):
    """Load a plot schema from an XML file 'path'.

    See 'savePlotSchema'."""

    document = loadAsDom(path)
    removeWhitespaceText(document)
    if len(document.childNodes) != 1 \
       or document.childNodes[0].nodeName != "plot-schema":
        raise ParseError, "document is not an XML plot schema"

    return _plotSchemaFromDom(document.childNodes[0])


