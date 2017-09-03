#!/usr/bin/python
# coding: utf8
from progressbar import (AdaptiveETA, AdaptiveTransferSpeed, Bar, Percentage,
                         ProgressBar)


class ProgressHandler(object):
    def __init__(self, media):

        progress_bar_widgets = [
            media.filename,
            "  ",
            Percentage(),
            Bar(),
            " ",
            AdaptiveTransferSpeed(),
            "  ",
            AdaptiveETA(),
        ]

        self.progress_bar = ProgressBar(maxval=media.size,
                                        term_width=80,
                                        widgets=progress_bar_widgets)
        self.progress_bar.start()

    def update_progress(self, status):
        if not status or status.progress() == 1:
            self.progress_bar.finish()

        else:
            size_downloaded = status.progress() * status.total_size
            self.progress_bar.update(size_downloaded)

