import threading


class WorkPool:
    def __init__(self, concurrency):
        self.total_concurrency = concurrency
        self.works = []
        self.rlock = threading.RLock()

    def start_work(self, func, sym):

        if len(self.works) >= self.total_concurrency:
            w = self.works[0]
            w.join()
            self.works = self.works[1:]
        w = threading.Thread(target=func, args=(sym, ))
        self.works.append(w)
        w.start()

    def start_work_arg2(self, func, arg1, arg2):
        if len(self.works) >= self.total_concurrency:
            w = self.works[0]
            w.join()
            self.works = self.works[1:]
        w = threading.Thread(target=func, args=(arg1, arg2, ))
        self.works.append(w)
        w.start()

    def wait_for_all(self):
        for w in self.works:
            w.join()

    def lock(self):
        self.rlock.acquire()

    def unlock(self):
        self.rlock.release()
