import os

from threading import Thread

import datetime


class ShotImageProcess(Thread):
    def __init__(self, task_queue, save_path):
        Thread.__init__(self)
        self.save_path = save_path
        self.index_queue = task_queue

    def save(self, grab_image):
        now = datetime.datetime.now()

        stock_num = now.timestamp()
        image_name = "{}.jpg".format(stock_num)
        grab_image.save(os.path.join(self.save_path, image_name))

    def run(self):
        while True:
            grad_image = self.index_queue.get()
            self.save(grad_image)
            self.index_queue.task_done()


if __name__ == '__main__':
    pass
