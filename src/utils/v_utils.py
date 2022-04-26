import subprocess
import os
import sys
import hashlib


def hashString(input_string):
    return hashlib.sha256(
        input_string.encode()).hexdigest()[:12]


def openPdfFile(file_path):
    file_path = "okular \"" + file_path + "\""

    print("running " + file_path)
    FNULL = open(os.devnull, 'w')
    subprocess.Popen([file_path], shell=True, stdout=FNULL,
                     stderr=subprocess.STDOUT)


def findFile(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)


def printProgress(iteration, total,
                  prefix='', suffix='', decimals=1, barLength=50):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """

    formatStr = "{0:." + str(decimals) + "f}"
    percent = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = '*' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' %
                     (prefix, bar, percent, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


def constant(f):
    def fset(self, value):
        raise TypeError

    def fget(self):
        return f()
    return property(fget, fset)


def frange(x, y, jump):
    while x < y:
        yield x
        x += jump


def print_vars(obj):
    fields = vars(obj)
    print(', '.join("%s: %s" % item for item in fields.items()))


def findFilesByExtention(input_path, extension="pdf"):
    file_list = []
    if os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            for file in files:
                if file.endswith("." + extension):
                    file_list.append(os.path.join(root, file))
    else:
        file_list.append(input_path)

    return file_list
