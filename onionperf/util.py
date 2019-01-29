'''
  OnionPerf

  Authored by Rob Jansen, 2015

  Documentation by Ana Custura 2019

  See LICENSE for licensing information

'''

import sys, os, socket, logging, random, re, shutil, datetime, urllib
from subprocess import Popen, PIPE, STDOUT
from threading import Lock
from cStringIO import StringIO
from abc import ABCMeta, abstractmethod

LINEFORMATS = "k-,r-,b-,g-,c-,m-,y-,k--,r--,b--,g--,c--,m--,y--,k:,r:,b:,g:,c:,m:,y:,k-.,r-.,b-.,g-.,c-.,m-.,y-."

def make_dir_path(path):
    '''
    This function creates a directory if it does not exist, expanding the path as required.

    :param path: Path to create
    :type path: string
    
    '''
    p = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(p):
        os.makedirs(p)

def find_file_paths(searchpath, patterns):
    '''
    This function recursively searches a path for filenames matching a given set of patterns.

    :param searchpath: Path to search
    :type searchpath: string
    :param patterns: Name patterns to search for
    :type patters: string

    :returns: list
    '''

    paths = []
    if searchpath.endswith("/-"): paths.append("-")
    else:
        for root, dirs, files in os.walk(searchpath):
            for name in files:
                found = False
                fpath = os.path.join(root, name)
                fbase = os.path.basename(fpath)
                for pattern in patterns:
                    if re.search(pattern, fbase): found = True
                if found: paths.append(fpath)
    return paths

def find_file_paths_pairs(searchpath, patterns_a, patterns_b):
    '''
    This function recursively searches a path for filenames matching two sets of given patterns.

    :param searchpath: Path to search
    :type searchpath: string
    :param patterns_a: First set of name patterns to search for
    :type patters: string
    :param patterns_b: Second set of name patterns to search for
    :type patters: string

    :returns: list
    '''


    paths = []
    for root, dirs, files in os.walk(searchpath):
        for name in files:
            fpath = os.path.join(root, name)
            fbase = os.path.basename(fpath)

            paths_a = []
            found = False
            for pattern in patterns_a:
                if re.search(pattern, fbase):
                    found = True
            if found:
                paths_a.append(fpath)

            paths_b = []
            found = False
            for pattern in patterns_b:
                if re.search(pattern, fbase):
                    found = True
            if found:
                paths_b.append(fpath)

            if len(paths_a) > 0 or len(paths_b) > 0:
                paths.append((paths_a, paths_b))
    return paths

def find_path(binpath, defaultname):
    '''
    This function finds and returns the path to a named binary.

    :param binpath: Path to the binary
    :type binpath: string
    :param defaultname: Name of the binary
    :type defaultname: string

    :returns: string
    '''

    if binpath is not None:
        binpath = os.path.abspath(os.path.expanduser(binpath))
    else:
        w = which(defaultname)
        if w is not None:
            binpath = os.path.abspath(os.path.expanduser(w))
        else:
            logging.error("You did not specify a path to a '{0}' binary, and one does not exist in your PATH".format(defaultname))
            return None
    # now make sure the path exists
    if os.path.exists(binpath):
        logging.info("Using '{0}' binary at {1}".format(defaultname, binpath))
    else:
        logging.error("Path to '{0}' binary does not exist: {1}".format(defaultname, binpath))
        return None
    # we found it and it exists
    return binpath

def which(program):
    '''
    This function finds the path to a Program.

    :param program: Program to search for
    :type program: string

    :returns: string if a path was found or None otherwise
    '''
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

def timestamp_to_seconds(stamp):  # unix timestamp
    '''
    This function transforms an unix timestamp to seconds.

    :param timestamp: Unix timestamp in string format
    :type timestamp: string

    :returns: float
    '''
 
    return float(stamp)

def date_to_string(date_object):
    '''
    This function transforms a date object to a string

    :param date_object: Date object to be converted
    :type date_object: datetime

    :returns: string
    '''
 
    if date_object is not None:
        return "{:04d}-{:02d}-{:02d}".format(date_object.year, date_object.month, date_object.day)
    else:
        return ""

def do_dates_match(date1, date2):
    ''' Compares two date objects to see if they match on year, month and day
 
    :param date1: First date object 
    :type date1: datetime
    :param date2: Second date object 
    :type date2: datetime
 
    :returns: bool
    '''

    year_matches = True if date1.year == date2.year else False
    month_matches = True if date1.month == date2.month else False
    day_matches = True if date1.day == date2.day else False
    if year_matches and month_matches and day_matches:
        return True
    else:
        return False

def get_ip_address():
    ''' Returns the IP address of the host.
    This could be ported to python-ipaddress or pyroute2 when moving codebase to Python 3.
    :returns: string
    '''
    ip_address = None

    data = urllib.urlopen('https://check.torproject.org/').read()
    if data is not None and len(data) > 0:
        ip_list = re.findall(r'[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}', data)
        if ip_list is not None and len(ip_list) > 0:
            ip_address = ip_list[0]

    if ip_address is None:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 53))
        ip_address = s.getsockname()[0]
        s.close()

    return ip_address

def get_random_free_port():
    ''' Picks a random high port and returns it if available.
 
    :returns: int
    '''

    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = random.randint(10000, 60000)
        rc = s.connect_ex(('127.0.0.1', port))
        s.close()
        if rc != 0: # error connecting, port is available
            return port

class DataSource(object):
    '''Class which models all data sources which can be used for onionperf analysis.
    Handles: simple files, xz compressed files and stdin input.
    '''
    def __init__(self, filename, compress=False):
        '''Initializes data source.

        :param filename: File name of data source 
        :type filename: string
        :param compress: Whether or not the file is compressed 
        :type compress: bool

        '''

        self.filename = filename
        self.compress = compress
        self.source = None
        self.xzproc = None

    def __iter__(self):

        if self.source is None:
            self.open()
        return self.source

    def next(self):
        '''
        Gets the next block of the data source.   
      
        '''
        return self.__next__()

    def __next__(self):  # python 3
        return self.source.next() if self.source is not None else None

    def open(self):
        '''
        Handles data source logic and sets the data source.

        '''
        if self.source is None:
            if self.filename == '-':
                self.source = sys.stdin
            elif self.compress or self.filename.endswith(".xz"):
                self.compress = True
                cmd = "xz --decompress --stdout {0}".format(self.filename)
                xzproc = Popen(cmd.split(), stdout=PIPE)
                self.source = xzproc.stdout
            else:
                self.source = open(self.filename, 'r')

    def get_file_handle(self):
        '''Returns data source, calling open() to set it if not set.
 
        :returns: file 
        '''
        if self.source is None:
            self.open()
        return self.source

    def close(self):
        '''Closes the data source and waits for xz process to finish.

        '''
        if self.source is not None: self.source.close()
        if self.xzproc is not None: self.xzproc.wait()


class Writable(object):
    '''Abstract class for modelling writables'''
    __metaclass__ = ABCMeta

    @abstractmethod
    def write(self, msg):
        '''Writes a message to writable'''
        pass

    @abstractmethod
    def close(self):
        '''Cleanly closes writable'''
        pass

class FileWritable(Writable):
    '''Implements the abstract Writable class for writable files'''

    def __init__(self, filename, do_compress=False, do_truncate=False):
        '''Initializes writable files
    
        :param filename: Name of file writable
        :type filename: string
        :param do_compress: Whether to compress the file 
        :type do_compress: bool
        :param do_truncate: Whether to truncate the file 
        :type do_truncate: bool
        '''
        self.filename = filename
        self.do_compress = do_compress
        self.do_truncate = do_truncate
        self.file = None
        self.xzproc = None
        self.ddproc = None
        self.lock = Lock()

        if self.filename == '-':
            self.file = sys.stdout
        elif self.do_compress or self.filename.endswith(".xz"):
            self.do_compress = True
            if not self.filename.endswith(".xz"):
                self.filename += ".xz"

    def write(self, msg):
        '''Writes a message to the file writable

        :param msg: Message to write
        :type msg: string
        '''
        self.lock.acquire()
        if self.file is None: self.__open_nolock()
        if self.file is not None: self.file.write(msg)
        self.lock.release()

    def open(self):
        '''Opens file writable'''
        self.lock.acquire()
        self.__open_nolock()
        self.lock.release()

    def __open_nolock(self):
        if self.do_compress:
            self.xzproc = Popen("xz --threads=3 -".split(), stdin=PIPE, stdout=PIPE)
            dd_cmd = "dd of={0}".format(self.filename)
            # # note: its probably not a good idea to append to finalized compressed files
            # if not self.do_truncate: dd_cmd += " oflag=append conv=notrunc"
            self.ddproc = Popen(dd_cmd.split(), stdin=self.xzproc.stdout, stdout=open(os.devnull, 'w'), stderr=STDOUT)
            self.file = self.xzproc.stdin
        else:
            self.file = open(self.filename, 'w' if self.do_truncate else 'a', 0)

    def close(self):
        '''Closes file writable'''
        self.lock.acquire()
        self.__close_nolock()
        self.lock.release()

    def __close_nolock(self):
        if self.file is not None:
            self.file.close()
            self.file = None
        if self.xzproc is not None:
            self.xzproc.wait()
            self.xzproc = None
        if self.ddproc is not None:
            self.ddproc.wait()
            self.ddproc = None

    def rotate_file(self, filename_datetime=datetime.datetime.now()):
        '''Rotates file writable and returns filename used for rotation.
           It closes and moves the old file and opens a new file at the original location.

        :param filename_datetime: Date to use for filename rotation
        :type filename_datetime: datetime

        '''
        self.lock.acquire()

        # build up the new filename with an embedded timestamp
        base = os.path.basename(self.filename)
        base_noext = os.path.splitext(os.path.splitext(base)[0])[0]
        ts = filename_datetime.strftime("%Y-%m-%d_%H:%M:%S")
        new_base = base.replace(base_noext, "{0}_{1}".format(base_noext, ts))
        new_filename = self.filename.replace(base, "log_archive/{0}".format(new_base))

        make_dir_path(os.path.dirname(new_filename))

        # close and move the old file, then open a new one at the original location
        self.__close_nolock()
        # shutil.copy2(self.filename, new_filename)
        # self.file.truncate(0)
        shutil.move(self.filename, new_filename)
        self.__open_nolock()

        self.lock.release()
        # return new file name so it can be processed if desired
        return new_filename

class MemoryWritable(Writable):
    '''Implements the Writable class for memory buffers
    '''

    def __init__(self):
        self.str_buffer = stringIO()

    def write(self, msg):
        '''Writes a message to the memory buffer

        :param msg: Message to write
        :type msg: string
        '''
        self.str_buffer.write()

    def readline(self):
        '''Returns a line from the buffer

        :returns: string
        '''
        return self.str_buffer.readline()

    def close(self):
        '''Closes memory buffer'''
        self.str_buffer.close()
