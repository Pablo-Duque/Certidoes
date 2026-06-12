import threading
import queue
from typing import Tuple, Any

Result = Tuple[bool, Any]


class BotWorker:
    def __init__(self):
        self._tasks = queue.Queue()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._bot = None
        self._running = True
        self._worker_thread_started = False
        self._thread.start()
        self._worker_thread_started = True

    def init_bot(self, on_ready=None, poll_interval=0.1):
        if on_ready is None:
            return

        def waiter():
            import time

            while self._bot is None and self._running:
                time.sleep(poll_interval)
            try:
                if self._bot is not None:
                    on_ready()
            except Exception as e:
                print("Erro no callback on_ready:", e)

        threading.Thread(target=waiter, daemon=True).start()

    def submit(self, cnpj, keys):
        if not self._running:
            raise RuntimeError("Thread parou")
        result_queue = queue.Queue(maxsize=1)
        self._tasks.put((cnpj, keys, result_queue))
        return result_queue

    def stop(self):
        self._running = False
        if self._bot is not None:
            self._bot.close()
        self._tasks.put((None, None, None))
        self._thread.join()

    def _worker_loop(self):
        from certidoes import Bot

        self._bot = Bot()
        while self._running:
            item = self._tasks.get()
            try:
                cnpj, keys, result_queue = item
                if cnpj is None and keys is None and result_queue is None:
                    break
                if cnpj == "__callable__" and callable(keys):
                    init_callable = keys
                    init_callable()
                    continue
                if self._bot is None:
                    raise RuntimeError("Bot não inicializado")
                try:
                    result = self._bot.search(cnpj, keys)
                    result_queue.put((True, result))
                except Exception:
                    result_queue.put((False, None))
            finally:
                self._tasks.task_done()
        if hasattr(self._bot, "close"):
            try:
                self._bot.close()
            except Exception:
                pass