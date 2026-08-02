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
