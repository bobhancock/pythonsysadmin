"""
	Generate a password.
"""
from random import Random

class Password:
    def __init__(self, len_passwd):
        self.lenPassword = len_passwd
        self.allnums = '1234567890'
        self.allsymbols = '#$%-!&'
        self.letters_lower = 'abcdefghijklmonpqrstuvwxyz'
        self.letters_upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.allletters = self.letters_lower + self.letters_upper

    def strong(self):
        """ Return a strong password """

        passwordLength = self.lenPassword 
        rng = Random()

        setNums = set(frozenset(self.allnums))
        setSymbols = set(frozenset(self.allsymbols))
        setLettersLower = set(frozenset(self.letters_lower))
        setLettersUpper = set(frozenset(self.letters_upper))
        #setLetters = set(frozenset(self.allletters))

        allchars = self.allnums + self.allletters + self.allsymbols

        password = ''
        for i in range(passwordLength):
        #while len(password) < passwordLength:
            password = password +  rng.choice(allchars)

        setPassword = set(frozenset(password))
        # keep a list of indices for places in password already changed
        listIndicesChanged = []

        # Does it contain a number?
        if len(setNums.intersection(setPassword)) == 0:
            # you need to add a number char to the password
            # pick a random place GT 5
            idxNum = rng.choice(range(5, passwordLength - 1))
            # pick a random number
            num = rng.choice(self.allnums)
            password = password[:idxNum] + num + password[idxNum:]
            setPassword = set(frozenset(password))
            listIndicesChanged.append(idxNum)

        # Does it contain at least one lowercase letter
        if len(setLettersLower.intersection(setPassword)) == 0:
            idx_lowletter = rng.choice(range(5, passwordLength - 1))
            while idx_lowletter in listIndicesChanged:
                idx_lowletter = rng.choice(range(5, passwordLength - 1))

            listIndicesChanged.append(idx_lowletter)

            # pick a random lowercase letter
            lowletter = rng.choice(self.letters_lower)
            password = password[:idx_lowletter] + lowletter + password[idx_lowletter:]
            setPassword = set(frozenset(password))

        # Does it contain at least one uppercase letter
        if len(setLettersUpper.intersection(setPassword)) == 0:
            idx_upperletter = rng.choice(range(5, passwordLength - 1))
            while idx_upperletter in listIndicesChanged: 
                idx_upperletter = rng.choice(range(5, passwordLength - 1))

            listIndicesChanged.append(idx_upperletter)

            # pick a random uppercase letter
            upperletter = rng.choice(self.letters_upper)
            password = password[:idx_upperletter] + upperletter + password[idx_upperletter:] 
            setPassword = set(frozenset(password))

        # chars 2-6 must contain at least one symbol
        setPassword_stub = set(frozenset(password[2:6]))
        if len(setSymbols.intersection(setPassword_stub)) == 0:
            idx_symbol = rng.choice(range(1, 5))
            while idx_symbol in listIndicesChanged:
                idx_symbol = rng.choice(range(1, 5))

            symbol = rng.choice(self.allsymbols)
            password = password[:idx_symbol] + symbol + password[idx_symbol+1:]

        return password

