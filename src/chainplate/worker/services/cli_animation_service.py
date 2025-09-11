import itertools
import threading
import sys
import time

def loading_spinner(done_flag, message="", interval=0.1):
    for c in itertools.cycle([' | ', ' / ', ' - ', ' \\ ']):
        if done_flag.is_set():
            break
        sys.stdout.write(f"\r{message} {c}")
        sys.stdout.flush()
        time.sleep(interval)      
    sys.stdout.write('\x1b[2K')
    sys.stdout.flush()

def run_with_spinner(action, *args, message="Loading...", **kwargs):
    done_flag = threading.Event()
    spinner_thread = threading.Thread(
        target=loading_spinner, args=(done_flag, message), daemon=True
    )
    spinner_thread.start()

    try:
        result = action(*args, **kwargs)
    finally:
        done_flag.set()
        spinner_thread.join()

    return result
