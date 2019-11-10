

def screen_resolution():
    try:
        import subprocess
        cmd = ['xrandr']
        cmd2 = ['grep', '*']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(cmd2, stdin=p.stdout, stdout=subprocess.PIPE)
        p.stdout.close()
        
        resolution_string, junk = p2.communicate()
        resolution = resolution_string.split()[0]
        width, height = str(resolution)[2:-1].split('x')
        return int(width),int(height)
    except:
        import ctypes
        user32 = ctypes.windll.user32
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

        return screensize