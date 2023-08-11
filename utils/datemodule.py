from datetime import date, timedelta

DATE_FORMAT = "%Y-%m-%d"

def getStartEndDate(timePeriod='6m'):
    duration = timePeriod[:-1]
    timeSymbol = timePeriod[-1]
    
    days = 6 * 30
    if (timeSymbol.upper() == 'D'):
        days = int(duration)
    elif (timeSymbol.upper() == 'W'):
        days = int(duration)*7
    elif (timeSymbol.upper() == 'M'):
        days = int(duration)*30
    elif (timeSymbol.upper() == 'Y'):
        days = int(duration)*365

    today = date.today()
    start_date = (today - timedelta(days=days))
    end_date = today

    return start_date, end_date


def getStartEndDateString(timePeriod='6m'):
    start, end = getStartEndDate(timePeriod)
    return start.strftime(DATE_FORMAT), end.strftime(DATE_FORMAT)


def getDateRange(start_date, end_date):
    for n in range(int((end_date - start_date).days)+1):
        yield start_date + timedelta(n)