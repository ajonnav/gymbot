from __future__ import print_function
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import boto3
import os
import pytz

GENERAL_ERROR_MSG = 'Whoa dude, something went wrong - I can\'t tell who sent me this message'
INVALID_ACTION_MSG = 'Whoa dude, send me something valid'
IB_COLUMN = 2
EM_COLUMN = 3
ANI_COLUMN = 4
ROW_OFFSET = 2
SHEET_NAME = os.environ['SHEET_NAME']
BUCKET = os.environ['BUCKET']
CREDS_FILE = os.environ['CREDS_FILE']
TZ = os.environ['TIMEZONE']
GSHEET_SCOPE = 'https://www.googleapis.com/auth/spreadsheets'


def lambda_handler(event, context):
    print("Received event: " + str(event))
    if "Body" not in event or not event["Body"]:
        return twiliofy(INVALID_ACTION_MSG)
    body = event["Body"].lower()

    if "From" not in event or not event["From"]:
        return twiliofy(GENERAL_ERROR_MSG)
    sender = event["From"]

    wks = get_worksheet()

    now = get_current_datetime()

    if "count" in body:
        ret_str = tallies_to_string(get_tallies(wks, now))
        return twiliofy(ret_str)

    elif "gym" in body:
        retStr = tallies_to_string(increase_tally(wks, now, sender))
        return twiliofy('Yay you went to the gym! Here are the tallies for everyone:\n' + retStr)

    else:
        return twiliofy(INVALID_ACTION)


def get_worksheet():
    s3 = boto3.resource('s3')
    obj = s3.Bucket(BUCKET).Object(CREDS_FILE)
    scope = [GSHEET_SCOPE]
    credentials = ServiceAccountCredentials.from_json(obj.get()['Body'].read())
    credentials_with_scope = credentials.create_scoped(scope)
    gc = gspread.authorize(credentials_with_scope)
    wks = gc.open(SHEET_NAME).sheet1
    return wks


def tallies_to_string(tallies):
    ret_str = ''
    # tallies looks like this
    # {"weekly":{"Aibi": 1, "Ani": 2, "Emily": 3}, "total": {"Aibi": 1, "Ani": 2, "Em": 3}}
    for tally_type in tallies:
        ret_str = ret_str + tally_type + ':\n'
        for person in tallies[tally_type]:
            ret_str = ret_str + person + ' - ' + str(tallies[tally_type][person]) + '\n'
    return ret_str


def get_tallies(wks, now):
    return {"Weekly Tallies": get_weekly_tallies(wks, now), "Total Tallies": get_total_tallies(wks)}


def get_weekly_tallies(wks, now):
    tallies = {}
    (start, end) = get_start_end_rows(now)
    ibCells = wks.range(start, IB_COLUMN, end, IB_COLUMN)
    emCells = wks.range(start, EM_COLUMN, end, EM_COLUMN)
    aniCells = wks.range(start, ANI_COLUMN, end, ANI_COLUMN)
    count = 0
    for cell in ibCells:
        if cell.value != '':
            count = count + 1
    tallies["Aibi"] = count
    count = 0
    for cell in emCells:
        if cell.value != '':
            count = count + 1
    tallies["Emily"] = count
    count = 0
    for cell in aniCells:
        if cell.value != '':
            count = count + 1
    tallies["Ani"] = count
    return tallies


def get_start_end_rows(now):
    dayNumber = get_day_number(now)
    start = (dayNumber - 1) / 7 * 7 + 1 + ROW_OFFSET
    end = dayNumber + ROW_OFFSET
    return (start, end)


def get_total_tallies(wks):
    cells = wks.range(ROW_OFFSET, IB_COLUMN, ROW_OFFSET, ANI_COLUMN)
    tallies = {"Aibi": cells[0].value, "Emily": cells[1].value, "Ani": cells[2].value}
    return tallies


def increase_tally(wks, now, sender):
    todayRow = get_row_for_datetime(now)
    if wks.cell(todayRow, 1).value == '':
        wks.update_cell(todayRow, 1, str(now.strftime("%A %x")))
    senderColumn = get_sender_column(sender)
    if senderColumn < 0:
        print("Could not recognize sender: " + sender)
    elif wks.cell(todayRow, senderColumn).value == '':
        wks.update_cell(todayRow, senderColumn, now.strftime("%H:%M"))
    return get_tallies(wks, now)


def get_sender_column(sender):
    if "2645" in sender:
        return ANI_COLUMN
    elif "5182" in sender:
        return IB_COLUMN
    elif "7043" in sender:
        return EM_COLUMN
    else:
        return -1


def get_row_for_datetime(date_time):
    dayNumber = get_day_number(date_time)
    return dayNumber + 2


def get_day_number(date_time):
    return int(date_time.strftime("%j"))


def get_current_datetime():
    return datetime.datetime.now(pytz.timezone(TZ))


def twiliofy(body):
    return '<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message>' + body + '</Message></Response>'
