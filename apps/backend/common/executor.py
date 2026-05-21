"""Background task execution abstraction.

Provides a seam for thread creation so tests can inject a synchronous
runner instead of mocking threading.Thread globally.

Usage in production::

    from common.executor import background

    background.run(target=my_func, args=(arg1,), name="my-task")

Usage in tests::

    from common.executor import SameThreadRunner

    # Replace the runner
    background = SameThreadRunner()
    background.run(target=my_func, args=(arg1,))
    # my_func executes synchronously here
"""

import threading
from collections.abc import Callable
from typing import Any


class BackgroundRunner:
    """Wraps ``threading.Thread`` — the default production runner."""

    def run(
        self,
        target: Callable[..., Any],
        args: tuple[Any, ...] = (),
        name: str | None = None,
    ) -> None:
        thread = threading.Thread(target=target, args=args, daemon=True, name=name)
        thread.start()


class SameThreadRunner:
    """Executes the target synchronously in the current thread — for tests.

    Usage::

        from common.executor import SameThreadRunner

        runner = SameThreadRunner()
        runner.run(target=my_func, args=(arg1,))
        # my_func has already completed here
    """

    def run(
        self,
        target: Callable[..., Any],
        args: tuple[Any, ...] = (),
        name: str | None = None,
    ) -> None:
        target(*args)


# Module-level default runner — importable as ``from common.executor import background``
background: BackgroundRunner = BackgroundRunner()
