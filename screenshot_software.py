import os
import shutil
import sys
import traceback
from queue import Queue
from time import sleep

import win32api
import win32con
from PIL import ImageGrab
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

from utils.utils import get_window_handle, show_window, screen_clicked, generate_path_names, hide_window
from shot_image_save import ShotImageProcess
from window_ui import Ui_MainWindow
from config import settings


class Window(Ui_MainWindow, QMainWindow):
    def __init__(self, parent):
        super(Window, self).__init__(parent)
        self.setupUi(self)
        # self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        ################################
        self.strategy_folder_path = []
        self.save_folder_path = None
        self.strategy_folders = None

        self.unclassified_folder = None
        self.deviate_folder = None
        self.synchronous_rise_5_folder = None
        self.synchronous_rise_15_folder = None
        self.synchronous_rise_daily_folder = None
        self.offset_breakthrough_folder = None

        self.unclassified_image_name_list = []
        self.current_image_path = None
        ###################################
        self.current_stock_type = None
        self.shot_num = None

        #################################
        self.shot_frequency = 3
        self.shotFrequencySpinBox.setValue(self.shot_frequency)
        self.shot_image_queue = Queue()
        self.shot_image_process_thread_num = 8

        ##################################
        self.handle = None

        ##################################

        self.shotFrequencySpinBox.setFocusPolicy(Qt.NoFocus)

        self.show_init_image()

    @pyqtSlot()
    def on_saveFolderButton_clicked(self):
        self.save_folder_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹", "daily_screenshot")

        if self.save_folder_path is not None and self.save_folder_path != "":
            QMessageBox.information(self, "信息", "选择文件夹成功！")

            self.strategy_folders = generate_path_names(self.save_folder_path,
                                                        settings.get('strategy').get('dir_name_tree'))

            for folder in self.strategy_folders:
                if not os.path.exists(folder):
                    os.makedirs(folder)
                self.update_lcd_num(folder)

            self.unclassified_folder = self.strategy_folders[0]
            self.deviate_folder = self.strategy_folders[1]
            self.synchronous_rise_5_folder = self.strategy_folders[2]
            self.synchronous_rise_15_folder = self.strategy_folders[3]
            self.synchronous_rise_daily_folder = self.strategy_folders[4]
            self.offset_breakthrough_folder = self.strategy_folders[5]

            self.unclassified_image_name_list = os.listdir(self.unclassified_folder)

            self.show_next_image()
        else:
            QMessageBox.critical(self, "错误", "请重新选择文件夹！")
            return

    @pyqtSlot()
    def on_deviateButton_clicked(self):
        if self.current_image_path is None:
            return
        self.move_image_update_nums(self.deviate_folder)

    @pyqtSlot()
    def on_synRise5Button_clicked(self):
        if self.current_image_path is None:
            return
        self.move_image_update_nums(self.synchronous_rise_5_folder)

    @pyqtSlot()
    def on_synRise15Button_clicked(self):
        if self.current_image_path is None:
            return
        self.move_image_update_nums(self.synchronous_rise_15_folder)

    @pyqtSlot()
    def on_synRiseDailyButton_clicked(self):
        if self.current_image_path is None:
            return
        self.move_image_update_nums(self.synchronous_rise_daily_folder)

    @pyqtSlot()
    def on_offsetBreakthroughButton_clicked(self):
        if self.current_image_path is None:
            return
        self.move_image_update_nums(self.offset_breakthrough_folder)

    @pyqtSlot()
    def keyPressEvent(self, QKeyEvent):
        # QKeyEvent.modifiers() == Qt.ControlModifier and
        if self.current_image_path is not None:
            if QKeyEvent.key() == Qt.Key_Up:
                self.move_image_update_nums(self.synchronous_rise_5_folder)
            elif QKeyEvent.key() == Qt.Key_Left:
                self.move_image_update_nums(self.synchronous_rise_15_folder)
            elif QKeyEvent.key() == Qt.Key_Right:
                self.move_image_update_nums(self.synchronous_rise_daily_folder)
            elif QKeyEvent.key() == Qt.Key_Down:
                self.move_image_update_nums(self.deviate_folder)
            elif QKeyEvent.key() == Qt.Key_0:
                self.move_image_update_nums(self.offset_breakthrough_folder)
            elif QKeyEvent.key() == Qt.Key_Delete:
                os.remove(self.current_image_path)
                self.update_lcd_num(self.unclassified_folder)
                self.show_next_image()

    def move_image_update_nums(self, strategy_folder):
        dst_path = os.path.join(strategy_folder, os.path.basename(self.current_image_path))
        shutil.move(self.current_image_path, dst_path)
        self.update_lcd_num(strategy_folder)
        self.update_lcd_num(self.unclassified_folder)
        self.show_next_image()

    @pyqtSlot()
    def on_screenShotButton_clicked(self):
        self.handle = get_window_handle('海王星')

        if self.user_selection_check() is False:
            return

        show_window(self.handle)

        screen_clicked(eval(settings.get('click_point_info').get('left_menu')))

        sleep_time = 1.0 / self.shot_frequency

        for x in range(self.shot_image_process_thread_num):
            worker = ShotImageProcess(self.shot_image_queue, self.unclassified_folder)
            worker.setDaemon(True)
            worker.start()

        try:
            for i in range(self.shot_num):
                grab_image = ImageGrab.grab((0, 0, 1920, 1080))
                win32api.keybd_event(settings.get('VK_CODE_info').get('down_arrow'), 0, 0, 0)
                win32api.keybd_event(settings.get('VK_CODE_info').get('down_arrow'), 0, win32con.KEYEVENTF_KEYUP, 0)
                self.shot_image_queue.put(grab_image)
                sleep(sleep_time)
        except MemoryError:
            message = traceback.format_exc()
            self.logger.error(message)
            exit(0)

        self.shot_image_queue.join()

        sleep(2)

        self.update_lcd_num(self.unclassified_folder)

        hide_window(self.handle)

        self.handle = get_window_handle('截图分类')
        show_window(self.handle)

        sleep(1)

        click = QMessageBox.information(self, "信息", "截图已完成")

        if click == QMessageBox.Ok:
            self.unclassified_image_name_list = os.listdir(self.unclassified_folder)
            self.show_next_image()

    # def update_stock_related_parameter(self, stock_type):
    #     self.current_stock_type = stock_type
    #     self.shot_num = settings.get('shot_num_info').get(self.current_stock_type)
    #
    # def switch_stock_type(self):
    #
    #     screen_clicked(settings.get('click_point_info').get('zi_xuan_gu'))
    #
    #     if self.current_stock_type == "gang":
    #         screen_clicked(settings.get('click_point_info').get('gang_gu'))
    #         screen_clicked(settings.get('click_point_info').get('gang_gu_tong'))
    #         screen_double_clicked(settings.get('click_point_info').get('gang_first'))
    #         screen_clicked(settings.get('click_point_info').get('left_menu'))
    #
    #     elif self.current_stock_type == "a":
    #         screen_clicked(settings.get('click_point_info').get('a_gu'))
    #         screen_double_clicked(settings.get('click_point_info').get('a_first'))
    #         find_indent_click(eval(settings.get('click_point_info').get('indent')))
    #         screen_clicked(settings.get('click_point_info').get('left_menu'))

    def on_shotFrequencySpinBox_valueChanged(self):
        self.shot_frequency = self.shotFrequencySpinBox.value()

    def on_shotNumSpinBox_valueChanged(self):
        self.shot_num = self.shotNumSpinBox.value()

    def user_selection_check(self):
        if self.handle is None:
            QMessageBox.critical(self, "错误", "请打开海王星股票软件！")
            return False

        if self.save_folder_path is None or self.save_folder_path == "":
            QMessageBox.critical(self, "错误", "请先选择文件夹！")
            return False

        return True

    def update_lcd_num(self, folder_path):
        num = len(os.listdir(folder_path))
        strategy = os.path.basename(folder_path)
        if strategy == '未分类':
            self.unclassifiedLcd.display(str(num))
        elif strategy == '背离':
            self.deviateLcd.display(str(num))
        elif strategy == '5分钟':
            self.synRise5Lcd.display(str(num))
        elif strategy == '15分钟':
            self.synRise15Lcd.display(str(num))
        elif strategy == '日线':
            self.synRiseDailyLcd.display(str(num))
        elif strategy == '相抵突破':
            self.offsetBreakthroughLcd.display(str(num))

    def show_init_image(self):
        pixmap = QPixmap('images/init.jpg')  # 按指定路径找到图片
        self.imageDisplay.setPixmap(pixmap)  # 在label上显示图片
        self.imageDisplay.setScaledContents(True)  # 让图片自适应label大小

    def show_next_image(self):
        if len(os.listdir(self.unclassified_folder)) != 0:
            self.current_image_path = os.path.join(self.unclassified_folder, self.unclassified_image_name_list.pop())
            pixmap = QPixmap(self.current_image_path)  # 按指定路径找到图片
            self.imageDisplay.setPixmap(pixmap)  # 在label上显示图片
            self.imageDisplay.setScaledContents(True)  # 让图片自适应label大小
        else:
            self.current_image_path = None
            self.show_init_image()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = Window(None)
    mw.show()
    sys.exit(app.exec_())
