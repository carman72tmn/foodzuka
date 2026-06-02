import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko
import time

def check_command(cmd_id):
    # This is a bit tricky because I don't know how the system stores background commands
    # But I can just use command_status tool from the model side.
    # Wait, the user wants me to use terminal.
    pass

if __name__ == "__main__":
    print("Please use the command_status tool directly.")
