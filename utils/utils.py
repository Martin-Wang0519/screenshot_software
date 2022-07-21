import os

import re

import time

import win32api
import win32con
import win32gui


def get_window_handle(name_begin):
    hwnd_list = []
    win32gui.EnumWindows(lambda hWnd, param: param.append(hWnd), hwnd_list)
    for handle in hwnd_list:
        match = re.match(name_begin, win32gui.GetWindowText(handle))
        if match is not None:
            return handle
    return None


def show_window(handle):
    # 最大化并显示在最前面
    win32gui.SendMessage(handle, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
    win32gui.ShowWindow(handle, win32con.SW_MAXIMIZE)
    win32gui.SetForegroundWindow(handle)


def hide_window(handle):
    win32gui.ShowWindow(handle, win32con.HIDE_WINDOW)


def screen_clicked(point):
    if isinstance(point, str):
        point = eval(point)
    win32api.SetCursorPos(point)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    time.sleep(1)


def screen_double_clicked(point):
    if isinstance(point, str):
        point = eval(point)
    win32api.SetCursorPos(point)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    time.sleep(1)


def generate_path_names(root, dir_name_tree):
    global _root, _dir_name_tree
    ans = []
    for dir_name in dir_name_tree:
        if isinstance(dir_name, dict):
            for k, v in dir_name.items():
                _root, _dir_name_tree = k, v

            for child in generate_path_names(_root, _dir_name_tree):
                ans.append(os.path.join(root, child))
        else:
            ans.append(os.path.join(root, dir_name))
    return ans


if __name__ == '__main__':
    pass
