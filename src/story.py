import os, sys
from datetime import datetime
from hashlib import md5
from string import punctuation

from cipher import zombify
import session as sess

def get_date():     # global function for getting date from the user in the absence of datetime object
    while True:
        try:
            year = int(raw_input('\nYear: '))
            month = int(raw_input('\nMonth: '))
            day = int(raw_input('\nDay: '))
            if datetime(year, month, day) > datetime.now():
                print sess.error, "Bah! You can't just time-travel into the future!"
                year, month, day = [None] * 3
                continue
            return datetime(year, month, day)
        except ValueError:
            print sess.error, 'Invalid input! Cannot parse the given date!'
            year, month, day = [None] * 3

def hashed(hash_function, text):     # global hashing function (may use MD5 or SHA-256)
    hash_object = hash_function()
    hash_object.update(text)
    return hash_object.hexdigest()

class Story(object):
    '''
    The 'Story' object has all the information necessary for invoking a particular story.
    For example, one can get its filename hash, the data contained in it,
    tell whether it should be encrypted or decrypted, whether it's new, etc.
    '''
    def __init__(self, session, when = None):
        if when == 'today' or when == 'now':
            self.date = datetime.now()
        elif type(when) is str:
            self.date = datetime.strptime(when, '%Y-%m-%d')
        else:
            self.date = get_date()
        self.path = os.path.join(session.location, self.get_hash())
        self.key = session.key      # have a copy of the password so that we don't always have to invoke Session

    def get_hash(self):
        return hashed(md5, self.date.strftime('Day %d (%B %Y)'))

    def get_path(self):     # return the path only if the file exists and it's not empty
        return self.path if os.path.exists(self.path) and os.path.getsize(self.path) else None

    def read_data(self):
        with open(self.path, 'rb') as file_data:
            return file_data.read()

    def write_data(self, data, mode = 'wb'):
        with open(self.path, 'wb') as file:
            file.write(data)

    def encrypt(self, echo = True):
        try:    # just to check whether a file has already been encrypted
            data = self.decrypt()
            print sess.error, "This file looks like it's already been encrypted.", \
                  "\nIt's never encouraged to use this algorithm for encryption more than once!"
            return
        except AssertionError:
            file_data = self.read_data()
            data = zombify('e', sess.newline.join(file_data.split('\r')), self.key)  # to strip '\r' from the lines
            self.write_data(data)
            if echo:
                print sess.success, 'Successfully encrypted the file! (filename hash: %s)' % self.get_hash()

    def decrypt(self, overwrite = False):
        data = zombify('d', self.read_data(), self.key)
        assert data         # checking whether decryption has succeeded
        if overwrite:       # we catch the AssertionError to indicate the wrong password input
            self.write_data(data)
        else:
            return data

    def write(self):
        sess.clear_screen()
        keystroke = 'Ctrl+C'
        if sys.platform == 'win32':
            print sess.warning, "If you're using the command prompt, don't press %s while writing!" % keystroke
            keystroke = 'Ctrl+Z and [Enter]'
        if self.get_path():
            try:                    # "Intentionally" decrypting the original file
                print '\nStory already exists! Appending to the current story...'
                print '(filename hash: %s)' % self.get_hash()
                self.decrypt(True)  # an easy workaround to modify your original story
            except AssertionError:
                print sess.error, "Bleh! Couldn't decrypt today's story! Check your password!"
                return
        data = [datetime.now().strftime('[%Y-%M-%d] %H:%M:%S\n')]
        try:
            stuff = raw_input("\nStart writing... (Once you've written something, press [Enter] to record it \
to the buffer. Further [RETURN] strokes indicate paragraphs. Press {} when you're done!)\n\n\t".format(keystroke))
            data.append(stuff)
        except (KeyboardInterrupt, EOFError):
            sleep(sess.capture_wait)
            print '\nNothing written! Quitting...'
            if self.get_path():
                self.encrypt(echo = False)
        while True:
            try:
                stuff = raw_input('\t')     # auto-tabbing of paragraphs (for each [RETURN])
                data.append(stuff)
            except (KeyboardInterrupt, EOFError):
                sleep(sess.capture_wait)
                break
        self.write_data('\n\t'.join(data) + '\n\n', 'a')
        self.encrypt(echo = False)
        if raw_input(sess.success + ' Successfully written to file! Do you wanna see it (y/n)? ') == 'y':
            self.view()

    def view(self, return_text = False):
        date_format = self.date.strftime('%B %d, %Y (%A)')
        try:
            data = self.decrypt()
        except AssertionError:
            print sess.error, "Baaah! Couldn't decrypt the story!"
        sess.clear_screen()
        split_data = data.split()
        for word in split_data:     # Simple word counter (ignoring the timestamp)
            if word not in punctuation:
                try:
                    timestamp = datetime.strptime(word, '[%Y-%m-%d]')
                    count += 2          # "2" for both date and time
                except ValueError:
                    pass
        start = "\nYour story from %s ...\n\n<----- START OF STORY -----> (%d words)\n\n"\
                % (date_format, len(split_data) - count)
        end = "<----- END OF STORY ----->"
        if return_text:
            return (data, start, end)
        print start, data, end
