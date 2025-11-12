from django.db import models
from django.db.models import Func
from calendar import monthrange
from datetime import date, datetime
import pytz

class Month(Func):
    function = 'EXTRACT'
    template = '%(function)s(MONTH from %(expressions)s)'
    output_field = models.IntegerField()

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, monthrange(year,month)[1])
    return datetime(year, month, day, tzinfo=pytz.timezone('Africa/Johannesburg'))