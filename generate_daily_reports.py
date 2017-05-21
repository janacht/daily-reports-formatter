# -*- coding: utf-8 -*-

import csv

MANDATORY_WEEKS = 2

WEEK = 'Week'
SICK_NOTE = 'Illness'
FLEXITIME_NOTE = 'Flexitime'
HOLIDAY_NOTE = 'Holiday'
DATE = 'Date'
WORKING_HOURS = 'Working hours'
ACTIVITIES = 'Activities'
MANDATORY_WEEKS_INFO = 'Missed days: {} ({} total)'
EXTRA_WEEKS_INFO = 'Extra days: {} ({} more to take)'

#WEEK = 'Woche'
#SICK_NOTE = 'Krankheitsbedingte Abwesenheit'
#FLEXITIME_NOTE = 'Gleitzeitabbau'
#HOLIDAY_NOTE = 'Gesetzlicher Feiertag'
#DATE = 'Datum'
#WORKING_HOURS = 'Arbeitszeit (h)'
#ACTIVITIES = 'Tätigkeiten'
#MANDATORY_WEEKS_INFO = 'Nachzuholende Tage: {} ({} insgesamt)'
#EXTRA_WEEKS_INFO = 'Nachgeholte Tage: {} ({} noch nachzuholen)'


class Activity(object):
    def __init__(self, activity_str):
        self.activity_str = activity_str


class Day(object):
    def __init__(self, date, state, working_hrs, note):
        self.date = date
        self.state = state
        self.working_hrs = working_hrs
        self.note = note
        self.activities = []
        
    def is_working_day(self):
        return self.state == 'WORK'

    def is_missed_day(self):
        return self.state == 'FLEXITIME' or self.state == 'SICK'


class Week(object):
    def __init__(self, idx, days):
        self.idx = idx
        self.days = days

    def get_working_days(self):
        return [day for day in self.days if day.is_working_day()]

    def get_missed_days(self):
        return [day for day in self.days if day.is_missed_day()]


class Period(object):
    def __init__(self, weeks, mandatory_weeks):
        self.weeks = weeks
        self.mandatory_weeks = mandatory_weeks

    def get_missed_days_at_end_of_week(self, week_idx):
        total_missed_days = 0
        for week in self.weeks:
            if self.week_is_in_mandatory_period(week.idx):
                total_missed_days += len(week.get_missed_days())
            else:
                total_missed_days -= len(week.get_working_days())

            if week_idx == week.idx:
                return total_missed_days

    def week_is_in_mandatory_period(self, week_idx):
        return week_idx < self.mandatory_weeks


def parse_day_csv(csv_row):
    date = csv_row[0]
    state = csv_row[1]
    if state == 'WORK':
        working_hrs = csv_row[2]
    else:
        working_hrs = 0
    if state == 'HOLIDAY':
        note = csv_row[2]
    else:
        note = ''
    return Day(date, state, working_hrs, note)


def parse_schedule(path):
    with open(path, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        week_idx = 0
        current_week_days = []
        weeks = []
        for row in csvreader:
            if len(row) == 0:
                weeks.append(Week(week_idx, current_week_days))
                week_idx += 1
                current_week_days = []
            else:
                current_week_days.append(parse_day_csv(row))
        weeks.append(Week(week_idx, current_week_days))
    return weeks


def generate_day_latex(day):    
    if day.state == 'WORK':
        latex_src = day.date + ' & ' + str(day.working_hrs) + ' & $\dlsh$ \\\\ \n'
        latex_src += '\\multicolumn{3}{l}{\\parbox{135mm}{% \n'
        latex_src += '\\begin{itemize} \n'
        for activity in day.activities:
            latex_src += '\\item ' + activity.activity_str + '\n'
        latex_src += '\\end{itemize}}} \\\\ \n'
    else:
        if day.state == 'SICK':
            text = '\\textit{'+SICK_NOTE+'}'
        elif day.state == 'FLEXITIME':
            text = '\\textit{'+FLEXITIME_NOTE+'}'
        elif day.state == 'HOLIDAY':
            if len(day.note) == 0:
                text = '\\textit{'+HOLIDAY_NOTE+'}'
            else:
                text = '\\textit{'+day.note+'}'
        else:
            raise RuntimeError('Invalid day state')
        working_hrs = 0
        latex_src = day.date+' & '+str(working_hrs)+' & '+text+' \\\\ \n'
    return latex_src

        
def generate_week_latex(period, week):
    latex_src = ('\\begin{table}[!ht]\n'
                 ''+WEEK+' '+str(week.idx+1)+'\n'
                 '\\begin{center}\n'
                 '\\begin{tabular}{llp{6cm}}\n'
                 '\\toprule\n'
                 ''+DATE+' & '+WORKING_HOURS+' & '
                 ''+ACTIVITIES+'\\\\ \n'
                 '\\midrule \n')
    
    for day in week.days:
        latex_src += generate_day_latex(day)

    total_missed_days = period.get_missed_days_at_end_of_week(week.idx)
    if period.week_is_in_mandatory_period(week.idx):
        missed_days = len(week.get_missed_days())
        supplementary_status = MANDATORY_WEEKS_INFO.format(missed_days,
                                                           total_missed_days)
    else:
        extra_days = len(week.get_working_days())
        supplementary_status = EXTRA_WEEKS_INFO.format(extra_days,
                                                       total_missed_days)

    latex_src += ('\\midrule \n'
                  '\\multicolumn{3}{l}{'+supplementary_status+'} \\\\ \n'
                  '\\bottomrule \n'
                  '\\end{tabular} \n'
                  '\\end{center} \n'
                  '\\end{table} \n')
    return latex_src


def read_activities(period, activities_file_path):
    with open(activities_file_path, 'r') as activities_file:
        week_idx = -1
        for line_idx, line in enumerate(activities_file.readlines()):
            line = line.strip()
            if line[:4] == 'Week':
                working_day_idx = 0
                week_idx += 1
                if line != 'Week {}'.format(week_idx+1):
                    raise RuntimeError('Invalid week (line {})'.
									   format(line_idx+1))
                current_week = period.weeks[week_idx]
                working_days = current_week.get_working_days()
            elif line[:2] == '- ':
                activity = Activity(line[2:])
                if working_day_idx >= len(working_days):
                    raise RuntimeError('Too many activities in week {}'.
                                       format(week_idx+1))
                current_day = working_days[working_day_idx]
                current_day.activities.append(activity)
            elif len(line) == 0:
                working_day_idx += 1
            else:
                raise RuntimeError('Parsing failed (line {})'.
                                   format(line_idx+1))


def check_empty_days(period):
	for week in period.weeks:
		for idx, day in enumerate(week.days):
			if day.is_working_day() and len(day.activities) == 0:
				print('Warning: Day {} in week {} has no activities'.
					  format(idx+1, week.idx+1))
	
	
def main():
    mandatory_weeks = MANDATORY_WEEKS
    weeks = parse_schedule('schedule.csv')
    period = Period(weeks, mandatory_weeks)
    read_activities(period, 'activities.txt')
    check_empty_days(period)
    latex_src = ''
    for week in period.weeks:
        latex_src += generate_week_latex(period, week) + '\n\n\n'
    with open('daily_reports.tex', 'w') as text_file:
        text_file.write(latex_src)


if __name__ == "__main__":
    main()
