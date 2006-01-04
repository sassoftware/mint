#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#

def truncateForDisplay(s, maxWords=10, maxWordLen=15):
    """Truncates a string s for display. May limit the number of words in the
    displayed string to maxWords (default 10) and the maximum number of
    letters in a word to maxWordLen (default 15).
    
    Raises ValueError if you give it insane values for maxWords and/or 
    maxWordLen."""

    import re

    # Sanity check args
    if ((maxWords < 1) or (maxWordLen < 1)):
        raise ValueError
    
    # Split the words on whitespace
    wordlist = re.split('[\ ]+', s)

    # If the number of words in the new wordlist exceeded maxWords, whack
    # them and append "....". This denotes that there is more text to follow.
    if (len(wordlist) > maxWords):
        del wordlist[maxWords:]
        wordlist.append('....')

    # Loop over the words in reverse order. If we find a word that is too
    # long, go ahead and truncate the word with "..." and then whack all 
    # words to the right.
    curr = len(wordlist) - 1
    while (curr >= 0):
        if len(wordlist[curr]) > maxWordLen:
            wordlist[curr] = (wordlist[curr])[:maxWordLen] + '...'
            del wordlist[curr+1:]
            break
        curr -= 1

    # Return the new wordlist joined with spaces.
    return ' '.join(wordlist)
