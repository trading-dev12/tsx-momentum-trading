import csv


def load_watchlist(filename):

    watchlist = []

    with open(filename, newline="") as file:
        reader = csv.reader(file)

        for row in reader:
            if row:
                watchlist.append(row[0])

    return watchlist