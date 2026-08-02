import contextlib
import io
import logging


@contextlib.contextmanager
def protected():
    """Run an action with stdout redirected away from the terminal.

    Some pdfpz functions (e.g. BooksCollection.save_books_collection,
    BooksCollection.load_books_collection) call print() directly. During
    curses.wrapper's raw-terminal mode, an unbuffered print() writes
    straight into the screen curses is managing and corrupts the TUI's
    rendering. Capturing it here (and discarding it) keeps those calls
    harmless without needing to touch pdfpz itself.
    """

    # pythonic disable logging problematic with tui
    logging.disable(logging.CRITICAL)
    try:
        # pythonic with contextlib to remove prints, logging from tui
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            yield
    finally:
        # pythonic re-enable logging problematic with tui
        logging.disable(logging.NOTSET)


#  for logging enabled try to use protected from future protect
class ProtectWithLogging:
    def protected(self):
        """Run an action with stdout/stderr, and every active logging
        handler's stream, redirected away from the terminal.

        pdfpz used to call print() directly, which redirect_stdout alone
        was enough to catch. It now logs via `logging` instead --
        pdfpz.core.logger calls logging.basicConfig() once at import time,
        which binds its handler's .stream to whatever sys.stderr *was* at
        that moment. That's a captured object reference, not a live lookup
        of sys.stderr -- so contextlib.redirect_stdout/redirect_stderr,
        which only swap the sys module's current attribute, have no effect
        on a handler built before they ever ran. Swapping each handler's
        .stream directly (and restoring it after) is what actually
        redirects it, regardless of when the handler was constructed.
        """
        buf = io.StringIO()
        handlers = logging.root.handlers
        original_streams = [getattr(h, "stream", None) for h in handlers]
        for h in handlers:
            if hasattr(h, "stream"):
                h.stream = buf
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                yield
        finally:
            for h, orig in zip(handlers, original_streams):
                if orig is not None:
                    h.stream = orig
