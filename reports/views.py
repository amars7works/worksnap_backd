import time
import requests
import base64
from datetime import datetime,timedelta,date
from calendar import monthrange

from rest_framework.decorators import api_view
from django.shortcuts import render
from django.http.response import JsonResponse
from django.db.models import Q
from django.shortcuts import render, HttpResponse,redirect
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from django.contrib.auth.models import User

from xlsxwriter.workbook import Workbook
from reports.models import ProjectsList,\
							UsersList,\
							UsersSummaryReport,\
							HolidayList,\
							UserDailyReport,\
							UserProfile,\
							RemainingAccruedLeaves
# Create your views here.

def user_register(request):
	if request.method == "POST":
		user_name,user_email,password,joined_date = (request.POST['user_name'],
			request.POST['user_email'],
			request.POST['password'],request.POST['joined_date'])
		user_profile = User.objects.create_user(username=user_name,
								 email=user_email,
								 password=password)
		user_profile = UserProfile.objects.create(user_name=user_name,
								 user_email=user_email,
								 password=password,
								 joined_date=joined_date)
		all_users=get_user_names()
		return render(request, 'login.html',{'all_users':all_users})
	else:
		return render(request, 'login.html',{'all_users':all_users})

def login_view(request):
	all_users=get_user_names()
	return render(request, 'login.html',{'all_users':all_users})

def logout_view(request):
	logout(request)
	return redirect("login")

def home(request):
	if request.method == "POST":
		username, password = request.POST['username'], request.POST['password']
		user = authenticate(username = username, password = password)
		if user is not None:
			login(request,user)
			user_name = request.user
			return render(request,'home.html',{'user':user_name})
			# return render(request,'worksnaps_report.html',{'all_users':all_users})
		else:
			return HttpResponse('{"error": "User does not exist"}')
	else:
		user_name = request.user
		return render(request,'home.html',{'user':user_name})

def worksnaps_report_html(request):
	user = request.user
	if user.is_superuser:
		all_users=get_user_names()
		return render(request,'worksnaps_report.html',{'all_users':all_users})
	else:
		return JsonResponse(
			{"Sorry dude you do not have permissions":"To access you must be super user"})

def daily_report_html(request):
	user = request.user
	if user.id == None:
		return JsonResponse(
			{"Sorry dude you do not have permissions":"To access you must be login"})
	else:
		all_users=get_user_names()
		return render(request,'dailyreport.html',{'all_users':all_users})

def registration_html(request):
	all_users=get_user_names()
	return render(request,'register.html',{'all_users':all_users})

def get_data(url):
	'''
		This function will work like get data from worksnaps
		Args: API end point
		Return: JSON data for given end point
	'''
	token = '23Mh2bkhQkUoqlU0KDfpVaYg9wXXsSgHr7YKdSm8'
	project_url = 'https://api.worksnaps.com/api/{}.json'.format(url)
	client_token = '{}:{}'.format(token,"ignored").encode()
	headers = {
		'Authorization':'Basic'+' '+base64.b64encode(client_token).decode('utf-8'),
		'Accept':'application/json',
		'Content-Type':'application/json',
	}
	request_data = requests.get(project_url,headers=headers)
	# print(request_data,"project data")
	request_data_json = request_data.json()
	
	return request_data_json

def get_summary(user_id,from_date,to_date):
	'''
		This function will work like get the user data from worksnaps
		Args: Worksnaps user id, From date and To date
		Return: JSON data for given user id
	'''
	user_ids = user_id
	name='manager_report'
	token = '23Mh2bkhQkUoqlU0KDfpVaYg9wXXsSgHr7YKdSm8'
	users_url = "https://api.worksnaps.com/api/summary_reports.json"
	client_token = '{}:{}'.format(token,"ignored").encode()
	headers = {
		'Authorization':'Basic'+' '+base64.b64encode(client_token).decode('utf-8'),
		'Accept':'application/json',
		'Content-Type':'application/json',
	}
	params={"from_date":from_date,"to_date":to_date,"user_ids":user_ids,"name":name}
	request_data = requests.get(users_url,headers=headers,params=params)
	request_data_json = request_data.json()
	# print(pprint.pprint(request_data_json))
	return request_data_json

def create_users(request):
	'''
		This function creates the list of user in DB who are available in Worksnaps
	'''
	user = request.user
	if user.is_superuser:
		users_qs = UsersList.objects.only('user_id')
		users_ids = [single_user.user_id for single_user in users_qs]
		worksnaps_users = get_data('users')
		print(users_ids,"-----")
		for i,value in enumerate(worksnaps_users.get("users")):
				if value.get('id',0) not in users_ids:
					print(value.get('id',0),"cooollllllll")
					UsersList.objects.create(
						user_id=value.get('id',''),user_email=value.get(
						'email',''),user_first_name=value.get(
						'first_name',''),user_last_name=value.get(
						'last_name',''),user_login_as=value.get('login',''))

		return JsonResponse({"Refresh":"Success"})
	else:
		return JsonResponse(
			{"Sorry dude you do not have permissions":"To access you nust be super user"})

def create_project(request):
	'''
		This function creates the list of projects in DB who are available in Worksnaps
	'''
	user = request.user
	if user.is_superuser:
		projects_qs = ProjectsList.objects.only('project_id')
		project_ids = [single_project.project_id for single_project in projects_qs]
		worksnaps_project = get_data('projects')
		for i,value in enumerate(worksnaps_project.get("projects")):
				if value.get('id',0) not in project_ids:
					ProjectsList.objects.create(
						project_id=value.get('id',''),project_name=value.get(
							'name',''),project_description=value.get(
							'description',''),project_status=value.get('status',''))

		return JsonResponse({"Refresh":"Success"})
	else:
		return JsonResponse(
			{"Sorry dude you do not have permissions":"To access you nust be super user"})

def convert_date_str_datetime(date_str):
	'''
		Convert the string date to date time object
		Args: date(in string)
		Return: date(date time object)
	'''
	date_datetime = datetime.strptime(date_str, '%Y-%m-%d')
	return date_datetime

def convert_date_datetime_str(create_datetime_obj):
	'''
		Convert the date object to string date
		Args: date(date time object)
		Return: date(in string)
	'''
	date_str = datetime.strftime(create_datetime_obj, '%Y-%m-%d')
	return date_str

def get_all_users_daily_data(from_date,to_date):
	users_qs = UsersList.objects.only('user_id')
	users_ids = [single_user.user_id for single_user in users_qs]
	current_date = to_date
	from_date = from_date
	while from_date < current_date:
		print(from_date,"from_date")
		to_date_datetime = from_date + timedelta(days = 1)
		from_date_str = convert_date_datetime_str(from_date)
		to_date_str = convert_date_datetime_str(to_date_datetime)
		for user_id in users_ids:
			worksnaps_summary = get_summary(user_id,from_date_str,to_date_str)
			print(worksnaps_summary,"user data")
			print(worksnaps_summary.get("manager_report"),"worksnaps_summary")
			if worksnaps_summary.get("manager_report"):
				print("Entered in to the first loop")
				for i,value in enumerate(worksnaps_summary.get("manager_report")):
					if to_date_str == value.get('date',0):
						UsersSummaryReport.objects.create(
							user_name=value.get('user_name',''),user_id=value.get(
								'user_id',''),date=value.get('date',''),duration=value.get(
								'duration_in_minutes',''),project_name=value.get(
								'project_name',''))
		from_date = from_date + timedelta(days = 1)

def create_users_summary(request):
	'''
		This function will store the all user Worksnaps data for given dates
	'''
	user = request.user
	if user.is_superuser:
		from_date = '2018-07-31'
		to_date = '2018-08-1'
		# summary_qs = UsersSummaryReport.objects.get(date=to_date)
		# users_ids = [single_date.user_id for single_date in summary_qs]
		users_qs = UsersList.objects.only('user_id')
		users_ids = [single_user.user_id for single_user in users_qs]
		current_date = convert_date_str_datetime(to_date)
		from_date = convert_date_str_datetime(from_date)
		while from_date < current_date:
			print(from_date,"from_date")
			to_date_datetime = from_date + timedelta(days = 1)
			from_date_str = convert_date_datetime_str(from_date)
			to_date_str = convert_date_datetime_str(to_date_datetime)
			for user_id in users_ids:
				worksnaps_summary = get_summary(user_id,from_date_str,to_date_str)
				print(worksnaps_summary,"user data")
				print(worksnaps_summary.get("manager_report"),"worksnaps_summary")
				if worksnaps_summary.get("manager_report"):
					print("Entered in to the first loop")
					for i,value in enumerate(worksnaps_summary.get("manager_report")):
						if to_date_str == value.get('date',0):
							UsersSummaryReport.objects.create(
								user_name=value.get('user_name',''),user_id=value.get(
									'user_id',''),date=value.get('date',''),duration=value.get(
									'duration_in_minutes',''),project_name=value.get(
									'project_name',''))
			from_date = from_date + timedelta(days = 1)

		return JsonResponse({"Refresh":"Success"})
	else:
		return JsonResponse(
			{"Sorry dude you do not have permissions":"To access you nust be super user"})

@api_view(['POST'])
def add_holiday_list(request):
	'''
		Able to add the custom holidays from frontend
	'''
	if request.method == 'POST':
		print(request.data,"printinf the date")
		holiday_date = request.data.get("date_h",'')
		holiday_description = request.data.get("holiday_description",'')
		day = request.data.get("day",'')
		HolidayList.objects.create(
			holiday_date=holiday_date,holiday_description=holiday_description,day=day)
	return JsonResponse({"Refresh":"Success"})


def working_days(year,month,from_date,to_date):
	'''
		Calculates the no of working days in a given month
	'''
	monthrang = monthrange(int(year),int(month))
	if monthrang[0] == 6 and monthrang[1] >= 30:
		no_of_working_days =  monthrang[1] - 6
	elif monthrang[0] == 5 and monthrang[1] >= 30:
		no_of_working_days =  monthrang[1] - 6
	elif monthrang[0] == 0:
		no_of_working_days =  monthrang[1] - 6
	else:
		no_of_working_days = monthrang[1] - 5
	holidays = HolidayList.objects.filter(
		Q(holiday_date__gte=from_date) & Q(holiday_date__lte=to_date))
	no_holidays = len(holidays)
	no_of_working_days = no_of_working_days - no_holidays
	return no_of_working_days,monthrang[0],monthrang[1]

def create_datetime_obj(sunday_date_str,year,month):
	'''
		create date objets for give month
	'''
	sun_sat_dates_datetime = []
	secons_sat = sunday_date_str[1]
	sun_sat_dates_datetime.append(date(int(year),int(month),secons_sat-1))
	for single_date in sunday_date_str:
		sun_sat_dates_datetime.append(date(int(year),int(month),single_date))
	return sun_sat_dates_datetime

def get_this_month_holidays(from_date,to_date):
	'''
		Get the holidays for the given month
	'''
	holiday_qs = HolidayList.objects.filter(
		Q(holiday_date__gte=from_date) & Q(
			holiday_date__lte=to_date))
	return [single_holiday.holiday_date for single_holiday in holiday_qs]

def create_month_days(no_days,year,month):
	'''
		Create a list of no of days
		Args: number of days
		Return: list of number of days
	'''
	whole_month_days = []
	for sing_day in range(0,no_days):
		whole_month_days.append(date(int(year),int(month),sing_day+1))
	return whole_month_days

def get_leave_dates(whole_month_days,no_dates):
	'''
		Get user leave dates
		Args:Whole month days(date objects),no of days user worked(date object)
		Return:No of leave dates
	'''
	leave_dates = list(set(whole_month_days) - set(no_dates))
	return leave_dates

def worked_on_weekenddays(user_worked_as_per_working_days,no_dates):
	'''
		Get the user worked on weekend days with dates
		Args:user worked with out weekend days,User worked dates
		Return: worked weekend days
	'''
	worked_weekend_days = list(set(no_dates)-set(user_worked_as_per_working_days))
	return worked_weekend_days

def time_worked_on_weeend_days(user_summary_qs,worked_weekend_days,total_duration):
	'''
		Calculate the time worked on weekend days worked
		Args:month query set,worked weekend days,total time worked
		Return:Time worked on weekend days
	'''
	extra_time_worked = []
	for single_date in user_summary_qs:
		for i,sing_day in enumerate(worked_weekend_days):
			if sing_day == single_date.date:
				extra_time = single_date.duration
				extra_time_worked.append(int(extra_time))
	return sum(extra_time_worked)


def get_user_names():
	user_list = UsersList.objects.all()
	user_name = []
	for single_user in user_list:
		first_name = single_user.user_first_name
		last_name = single_user.user_last_name
		username = first_name+' '+last_name
		user_name.append(username)
	user_name.append("s7_worksnaps")
	return sorted(user_name)

def create_from_to_date(year,month):
	monthrang = monthrange(int(year),int(month))
	from_date = year+'-'+month+'-'+'1'
	to_date = year+'-'+month+'-'+'{}'.format(monthrang[1])
	return from_date,to_date

def users_summary(from_date,to_date,year,month,user_name):
	'''
		Generate the user month report
	'''
	if year and month:
		month = month
		year = year
		from_date,to_date = create_from_to_date(year,month)
	if from_date:
		month = from_date.split('-')[1]
		year = from_date.split('-')[0]
	if user_name == 'all':
		# user_names = ["Rajender Reddy Garlapally","Vikash Babu Bendalam","Ananya Dodda",
		# "Mohan Krishna Y","Pavan Chand","Vignan Akoju","Venkatesh Marreboina",
		# "Mounika NagaHarish","Narendra Babu Ballilpalli","Ramya Ketha",'Swapna Bodduluri',
		# "Vinod Kumar Kurra","Mounika Bandaru","Naveen Kumar Katta","Mohiuddin Mohammed",
		# "Dileep Kumar Kommineni","Uday Kumar","kandukuri chary","Mani Sankar Nambaru",
		# "Mahesh Gorage","Atul Kumar","suresh kanchumati"]
		user_names = get_user_names()
	else:
		user_names = []
		user_names.append(user_name)
	data2 = {}
	for user_name in user_names:
		user_summary_qs = UsersSummaryReport.objects.filter(
			Q(date__gte=from_date) & Q(date__lte=to_date),user_name=user_name)
		# print(user_summary_qs,"user summary list")
		total_duration = []
		no_dates = []
		for single_date in user_summary_qs:
			time_done = single_date.duration
			total_duration.append(int(time_done))
			no_dates.append(single_date.date)

		no_working_days,month_start_day,days_in_month = working_days(year,month,from_date,to_date)
		sunday_start = 7-month_start_day
		list_hanig_sundays = []

		while sunday_start <= 31:
			list_hanig_sundays.append(sunday_start)
			sunday_start = sunday_start + 7

		list_sun_sat = create_datetime_obj(list_hanig_sundays,year,month)
		list_holidays = get_this_month_holidays(from_date,to_date)
		if list_holidays not in list_sun_sat:
			list_sun_sat.extend(list_holidays)

		month_holidays = list(set(list_sun_sat))
		whole_month_days = create_month_days(days_in_month,year,month)

		no_dates_holidays = []
		no_dates_holidays.extend(month_holidays)
		no_dates_holidays.extend(no_dates)

		leave_dates = get_leave_dates(whole_month_days,no_dates_holidays)
		user_worked_as_per_working_days = list(set(no_dates)-set(month_holidays))

		worked_weekend_days = worked_on_weekenddays(user_worked_as_per_working_days,no_dates)
		if worked_weekend_days:
			worked_on_weekend_days_holiday = "Yes"
			extra_time_worked = time_worked_on_weeend_days(
				user_summary_qs,worked_weekend_days,total_duration)
		else:
			worked_on_weekend_days_holiday = "No"
			extra_time_worked = 0
		total_time_to_work = (no_working_days-len(leave_dates)) * 480
		total_time_worked = sum(total_duration)
		#try:
		#	user_profile = UserProfile.objects.get(user_name=user_name)
		#	print(user_profile,"user profile")
		#	joined_date = user_profile.joined_date
		#	from_date_obj = convert_date_str_datetime(from_date)
		#	if joined_date > from_date_obj.date():
		#		print("dddddddd")
		#except:
		#	pass
		if user_name == "Bhanu Chandar Bala":
			leave_dates = []
		elif user_name == "Sai Bhaskar Ravuri":
			date_obj = date(2018,9,14)
			leave_dates = [date_obj]
		elif user_name == "Sushmasridurga DONTHAMSETTI":
                        leave_dates = []
		data = {
		'Name': user_name,
		'No of leaves' :  len(leave_dates),
		'Leave Dates' : leave_dates,
		'No of working days in August': no_working_days,
		'No of days worked': len(set(user_worked_as_per_working_days)),
		'For Month':'August',
		'Worked on weekend days or holidays':worked_on_weekend_days_holiday,
		'Dates Worked on weekend days':worked_weekend_days,
		'Time Worked on weekend days':extra_time_worked,
		"Total time to work":total_time_to_work,
		"Total time worked":total_time_worked,
		}
		data2[user_name] = data
	return data2,user_names
def username_excel(sheet1,user_names,cell_format):
	row = 1
	column = 0
	for i,single_user in enumerate(sorted(user_names)):
		if single_user != "Ikkurthi Manikanta" and single_user != "Saumya Garg" and single_user != "s7_worksnaps":
			sheet1.write(row,column,single_user)
			row = row + 1

def headers_data(sheet1,headers,cell_format):
	row = 0
	column = 1
	for i,single_header in enumerate(headers):
		sheet1.write(row,column,single_header,cell_format)
		column = column + 1

def change_date_format(dates):
	str_date = []
	if dates:
		for single_date in dates:
			date_time = single_date.isoformat()
			str_date.append(date_time)
		return str_date
	else:
		return '-'

def show_data(sheet1,user_names,headers,user_summary,cell_format):
	row = 1
	column = 0
	row_data = 1
	column_data = 1
	for key, user_data in sorted(user_summary.items()):
		if key != "Ikkurthi Manikanta" and key != "Saumya Garg" and key != "s7_worksnaps":
			sheet1.write(row_data,column_data,user_data.get('No of working days in August',"-"),cell_format)
			column_data = column_data + 1
			sheet1.write(row_data,column_data,user_data.get('No of days worked',"-"),cell_format)
			column_data = column_data + 1
			sheet1.write(row_data,column_data,user_data.get('No of leaves',"-"),cell_format)
			column_data = column_data + 1
			leave_dates = change_date_format(user_data.get('Leave Dates',"-"))
			sheet1.write(row_data,column_data,str(leave_dates),cell_format)
			column_data = column_data + 1
			sheet1.write(row_data,column_data,user_data.get('No of remainig leaves',''),cell_format)
			column_data = column_data + 1
			sheet1.write(row_data,column_data,user_data.get('Total time to work',"-"),cell_format)
			column_data = column_data + 1
			sheet1.write(row_data,column_data,user_data.get('Total time worked',"-"),cell_format)
			column_data = column_data + 1
			sheet1.write(row_data,column_data,user_data.get('Worked on weekend days or holidays',"-"),cell_format)
			column_data = column_data + 1
			sheet1.write(row_data,column_data,user_data.get('Time Worked on weekend days',"-"),cell_format)
			column_data = column_data + 1
			weekend_days = change_date_format(user_data.get('Dates Worked on weekend days',"-"))
			sheet1.write(row_data,column_data,str(weekend_days),cell_format)
			column_data = column_data + 1
			row_data = row_data + 1
			column_data = 1

def get_remaining_leaves():
	'''
		this function will return the remaing leaves of all employees
	'''
	remaining_leaves = RemainingAccruedLeaves.objects.all()
	# print(reminig_leaves)
	# ordered = sorted(reminig_leaves, key=operator.attrgetter('user'))
	# print(ordered)
	return remaining_leaves

def store_remaining_leaves(sheet1,remainig_leave,user_names):
	row_data = 0
	column_data = 5
	user_names_copy = user_names.copy()
	if len(user_names_copy) > 1:
		user_names_copy.remove('s7_worksnaps')
	for i,username in enumerate(user_names_copy):
		row_data = row_data + 1
		for single_user in remainig_leave:
			if username == single_user.user.username:
				sheet1.write(row_data,column_data,single_user.remaining_leaves)

def show_data_in_excel(request):
	month = request.GET.get("month",0)
	year = request.GET.get("year",2018)
	from_date = request.GET.get("from_date",0)
	to_date = request.GET.get("to_date",0)
	user_name = request.GET.get("user_name",0)
	if user_name == "all":
		user_summary,user_names = users_summary(from_date,to_date,year,month,user_name)
	else:
		user_summary,user_names = users_summary(from_date,to_date,year,month,user_name)
	# print(user_summary,"Data")

	# filename = '{}_raw_data_{}_to_{}.xlsx'.format(request.user.username,
	# 	from_date.strftime('%b_%d_%Y'),to_date.strftime('%b_%d_%Y'))
	response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	response['Content-Disposition'] = "attachment; filename=Worksnaps Report.xlsx"
	book = Workbook(response,{'in_memory': True})
	headers = ['No of working days in September','No of days worked','No of leaves','Leave Dates',
	'No of remaining leaves','Total time to work','Total time worked','Worked on weekend days or holidays',
	'Time Worked on weekend days','Dates Worked on weekend days']
	
	sheet1 = book.add_worksheet('Sep-2018')
	sheet1.freeze_panes(1, 1)
	sheet1.set_column('A:A',25)
	sheet1.set_row(0, 40)
	sheet1.set_column(1, 9, 15)
	cell_format = book.add_format()
	cell_format.set_text_wrap()
	cell_format.set_align('left')
	username_excel(sheet1,user_names,cell_format)
	headers_data(sheet1,headers,cell_format)
	show_data(sheet1,user_names,headers,user_summary,cell_format)
	remainig_leave = get_remaining_leaves()
	user_names = get_user_names()
	if user_name == "all":
		store_remaining_leaves(sheet1,remainig_leave,user_names)
	else:
		user_names = []
		user_names.append(user_name)
		store_remaining_leaves(sheet1,remainig_leave,user_names)
	book.close()

	return response

def store_daily_report(request):
	if request.method == "POST":
		username = request.user
		cretaed_at = request.POST.get("cretaed_at","Not filled anything")
		q1 = request.POST.get("q1","Not filled anything")
		q2 = request.POST.get("q2","Not filled anything")
		q3 = request.POST.get("q3","Not filled anything")
		q4 = request.POST.get("q4","Not filled anything")
		q5 = request.POST.get("q5","Not filled anything")
		UserDailyReport.objects.create(
			username=username,cretaed_at=cretaed_at,what_was_done_this_day=q1,
			what_is_your_plan_for_the_next_day = q2,
			what_are_your_blockers = q3,
			do_you_have_enough_tasks_for_next_three_days = q4,
			if_you_get_stuck_are_you_still_able_to_work_on_something_else = q5)
		messages.success(request, 'Daily report submitted')
		all_users=get_user_names()
		return render(request,'dailyreport.html',{'all_users':all_users})
	else:
		messages.error(request, 'Daily report did not submit')
		all_users=get_user_names()
		return render(request,'dailyreport.html',{'all_users':all_users})
