#----------------------------------------------------------------#
import os
from PIL import Image, ExifTags, ImageFile
import subprocess  		# запуск команд в командной строке операционной системы
import shutil 			# rmtree, copyfile и т.д. работа с файлами

import timeit
import inspect
import sys

import time
from datetime import datetime

import hashlib

import re #Импортируем регулярные выражения

import PIL.Image  # PIL.Image.MAX_IMAGE_PIXELS

#----------------------------------------------------------------#

from lib.CfgCreator import CfgCreator

#----------------------------------------------------------------#
def main():
	#-------------------------------------------------------------#

	ImageFile.MAXBLOCK = 2**20

	Image.MAX_IMAGE_PIXELS = None # убираем ограничение Pillow на размер фотографии

	#-------------------------------------------------------------#
	#                           Переменные
	# путь к директории в которой скрипт
	path_root = os.path.abspath(__file__) 	# определяет абсолютный путь в котором описан переданный объект
	path_root = os.path.realpath(path_root)	# возвращает канонический путь(приводит к нижнему регистру), убирая все символические ссылки (если они поддерживаются)
	path_root = os.path.dirname(path_root) 	# убираем имя скрипта из пути
	# путь к директории в которой лежит папка со скриптом, и файлы которые нужно обрабатывать
	path_dir = path_root[:( len(path_root) - len( os.path.split(path_root)[1] ) - 1 )]
	# имя директории со скриптом
	name_dir = path_root[( len(path_root) - len( os.path.split(path_root)[1] ) ):]

	#-------------------------------------------------------------#
	#                        вспомогательное
	def if_yes(inp):
		inp = inp.lower()
		return (inp == 'yes') or (inp == 'нуы') or (inp == 'да') or (inp == 'lf')
	def if_no(inp):
		inp = inp.lower()
		return (inp == 'no') or (inp == 'тщ') or (inp == 'нет') or (inp == 'ytn')

	jpg_name_temp = '7yp778ms3dfte9mq2fp58.jpg'

	# Опции, чтобы добавить новую опцию в программу - нужно вписать её сюда, создать для неё проверку, создать для неё переменную, добавить в вывод инфо о опциях
	list_config = [
		['изменять_только_метаинформацию', 'нет', ' (да, нет) Если включена эта опция изображения не будут перекодироваться. Соответственно эти опции не будут учитываться: quality, progressive, resize, resize_difference.'],
		['quality', '85', ' Качество от 1 до 95. Нет смысла использовать значения выше 95; 100 отключает части алгоритма сжатия JPEG и приводит к большим файлам(может быть больше оригинала) с отсутствием преимущества в качестве изображения.'],
		['progressive', 'оставить', ' (да, нет, оставить) Установка режима сохранения JPEG - Progressive или Baseline или использовать какой был.'],
		['resize', '100%', ' "100.0%" - не изменять размер. Можно указать например в таком формате "1024x1024" - тогда width hight будут не более указанной величины, пропорции в любом случае будут сохранятся.'],
		['resize_difference', '1px', ' Если изменение размера изображения по width или height меньше этой величины - то размер изображения не будет изменяться. Получается когда стоит 1px - изменять даже если разница в размерах 1px.'],
		['удалить_exif', 'нет', ' (да, нет) Удалить метаинформацию Exif из фотографий. Если вы храните свои фотографии, лучше не удалять Exif, мало ли зачем пригодятся метаданные.'],
		['удалить_превью', 'нет', ' (да, нет) Если стоят опции удалить_exif=да и удалить_превью=нет, то данные Exif удалятся кроме области превью(thumbnail).'],
		['восстановить_дату_изменения_файла', 'да', ' (да, нет) Скопировать дату и время снимка(из Exif) в дату изменения файла и дату открытия файла. Если даты снимка нет в Exif - оставить дату изменения и открытия как дата изменения у исходного файла.'],
		['повреждённые_фото', 'сохранить_превью', ' (пропустить, сохранить_превью) Можно настроить чтобы попытался сохранить превью в виде отдельного файла если фото повреждено.'],
		['спрашивать_подтверждение_на_замену', 'да', ' (да, нет) Спрашивать подтверждение на замену оригиналов для каждой папки/подпапки, либо спросить когда всё будет обработано.'] ]

	def cmd_exiftool(root, cmd, file_name_out, mess, time_modified, time_sec, changed):
		cmd = path_root[:3]+'"'+path_root[3:]+'"\\lib\\exiftool '+cmd  # оборачиваем в скобочки всю часть пути в которой могут быть пробелы, иначе cmd не поймёт
		PIPE = subprocess.PIPE
		os.chdir(root)  # переходим в папку с фотографией, поскольку ExifTool не понимает русские пути
		p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT)  # выполняем команду в ОС
		out = p.stdout.read()
		os.rename(jpg_name_temp, file_name_out)  # после read() переименовываем, иначе не будет гарантии что команда успела выполниться
		if out == b'    1 image files updated\r\n' :
			print(mess, end = '')
			if time_modified :
				os.utime(file_name_out, (time_sec, time_sec))
				print(' date time restore ', end='')
			print(' ок')
			changed = True
		else:
			out = str(out)[1:].replace('\\r', '').replace('\\n', '\n     ').replace('\\t', '').replace(jpg_name_temp, file_name_out)
			print('\n   ExifTool:'+out, end='\n  ')
			if ('1 image files updated' in out) and ('error' not in out.lower()) :
				print(mess, end = '')
				if time_modified :
					os.utime(file_name_out, (time_sec, time_sec))
					print(' date time restore ', end='')
				print(' ок')
				changed = True
		os.chdir(path_root)  # возвращаемся обратно в рабочую папку
		return changed

	def input_yes_no():
		while True :
			inp = input('Введите да или нет и нажмите Enter:')
			if if_yes(inp) :
				return True
			if if_no(inp) :
				return False

	#----------------------Инициализация--------------------------#

	# Сообщаем если скрипт запускают из странного места

	if (os.getcwd() != path_root) and (os.getcwd() != patch_dir):
		print('\n  Внимание!\n\nВы запускаете скрипт который лежит в директории:\n '+path_root+'\nСкрипт будет обрабатывать фото в директории:\n '+patch_dir)
		input('\nНажмите Enter для продолжения:')

	os.chdir(path_root)

	# Проверяем файл логов, если есть - работа скрипта была прервана в прошлый раз

	if os.path.isfile(path_root+'\\temp.log'):

		print('\n  Внимание!\n\nОбнаружено, что работа скрипта была прервана в прошлый раз.')
		print('  Введите yes или да - чтобы скрипт ПРОДОЛЖИЛ свою работу.')
		print('  Введите no или нет - чтобы скрипт начал работу ЗАНОВО.')
		inp = False
		while True :
			inp_str = input('Введите да или нет и нажмите Enter:')
			if if_yes(inp_str) :
				inp = True
				break
			else:
				if if_no(inp_str) :
					break
		
		if inp: # Продолжаем незавершённую работу
			# проверяем в той же ли папке лежит скрипт, может не в той
			# короче подумать тут ещё над этой логикой
			pass
		else:   # Хотят чтобы скрипт начал работу заново, спрашиваем, удалить ли временные файлы
			print('\n\nСкрипт начнёт обработку фото заново.')
			print('  Введите yes или да - чтобы скрипт УДАЛИЛ обработанные КОПИИ фотографий сделанные в прошлый раз.')
			print('  Введите no или нет - чтобы скрипт оставил копии.')
			pass

	else:

		# Инициализируем файл конфигурации, если есть считывает
		config = CfgCreator(path_root+'\\config.txt')

		def create_config():
			config.remove_spaces = False
			config.push(comment='')
			config.push(comment='-------------------Настройки конвертера JPEG-------------------')
			for i in range( len(list_config) ):
				config.push(comment='')
				config.push(list_config[i][0], list_config[i][1], comment = list_config[i][2], value_refresh=False)
			config.remove_spaces = True

		# определяем опции
		if os.path.isfile(config.path) :
			for i in range( len(list_config) ):
				config.push(list_config[i][0], list_config[i][1], comment = list_config[i][2], value_refresh=False)
		else:
			# файла нет - создаём с нашим оформлением по умолчанию
			create_config()

		# проверяем опции на корректность значений, декодируем значения
		change_only_meta_information = False
		quality = 85
		progressive = 1
		resize_relative = True
		resize_percent = 100.0
		resize_w = 1
		resize_h = 1
		resize_difference = 1
		remove_exif = False
		remove_preview = False
		save_preview = True
		time_modified = True
		damaged_photos = True
		ask_confirmation_to_replacement = False

		# 
		resize_difference_Show = True
		while True:

			b = True
			message = []

			# изменять_только_метаинформацию
			if not( if_yes(config.data['изменять_только_метаинформацию']) or if_no(config.data['изменять_только_метаинформацию']) ):
				message.append('изменять_только_метаинформацию - значением должно быть да или нет')
				b = False
			else:
				if if_yes(config.data['изменять_только_метаинформацию']):
					change_only_meta_information = True
			# quality
			mess = 'quality - значением должно быть целое число от 1 до 95, оптимально 85'
			try:
				if (int(config.data['quality']) < 1) or (int(config.data['quality']) > 100):
					message.append(mess)
					b = False
				else:
					quality = int(config.data['quality'])
			except ValueError:
				message.append(mess)
				b = False
			# progressive
			if not( if_yes(config.data['progressive']) or if_no(config.data['progressive']) or (config.data['progressive'].lower() == 'оставить') ):
				message.append('progressive - значением должно быть да или нет или оставить')
				b = 1
			else:
				if if_no(config.data['progressive']):
					progressive = 0
				elif if_yes(config.data['progressive']):
					progressive = 1
				else:
					progressive = 2
			# resize
			mess = 'resize - значение должно быть в таком формате 70% или 2048x2048'
			find_percent = re.findall('^([\d]+[.]?[\d]*)[\t\v ]*[%]$', config.data['resize'], flags=re.ASCII)
			find_absolute = re.findall('^([\d]+)[\t\v ]*[xXхХ][\t\v ]*([\d]+)$', config.data['resize'], flags=re.ASCII)
			if (find_percent) or (find_absolute):
				if find_percent :
					if (float(find_percent[0]) > 0) and (float(find_percent[0]) <= 100) :
						resize_percent = float(find_percent[0])
						if resize_percent == 100 :
							resize_difference_Show = False
					else:
						message.append(mess)
						b = False
				else:
					resize_relative = False
					resize_w = int(find_absolute[0][0])
					resize_h = int(find_absolute[0][1])
			else:
				message.append(mess)
				b = False
			# resize_difference
			if resize_difference_Show :
				mess = 'resize_difference - значение должно быть в таком формате 130px, >= 1px'
				find_diff = re.findall('^([\d]+)[\t\v ]*[pPрР][xXхХ]$', config.data['resize_difference'], flags=re.ASCII)
				if find_diff :
					if int(find_diff[0]) > 0 :
						resize_difference = int(find_diff[0])
					else:
						message.append(mess)
						b = False
				else:
					message.append(mess)
					b = False
			# удалить_exif
			if not( if_yes(config.data['удалить_exif']) or if_no(config.data['удалить_exif']) ):
				message.append('удалить_exif - значением должно быть да или нет')
				b = False
			else:
				if if_yes(config.data['удалить_exif']):
					remove_exif = True
			# удалить_превью
			if not( if_yes(config.data['удалить_превью']) or if_no(config.data['удалить_превью']) ):
				message.append('удалить_превью - значением должно быть да или нет')
				b = False
			else:
				if if_yes(config.data['удалить_превью']):
					remove_preview = True
			# восстановить_дату_изменения_файла
			if not( if_yes(config.data['восстановить_дату_изменения_файла']) or if_no(config.data['восстановить_дату_изменения_файла']) ):
				message.append('восстановить_дату_изменения_файла - значением должно быть да или нет')
				b = False
			else:
				if if_no(config.data['восстановить_дату_изменения_файла']):
					time_modified = False
			# повреждённые_фото
			if (config.data['повреждённые_фото'] != 'сохранить_превью') and(config.data['повреждённые_фото'] != 'пропустить') :
				message.append('повреждённые_фото - значением должно быть сохранить_превью или пропустить')
				b = False
			else:
				if config.data['повреждённые_фото'] == 'пропустить' :
					damaged_photos = False					
			# спрашивать_подтверждение_на_замену
			if not( if_yes(config.data['спрашивать_подтверждение_на_замену']) or if_no(config.data['спрашивать_подтверждение_на_замену']) ):
				message.append('спрашивать_подтверждение_на_замену - значением должно быть да или нет')
				b = False
			else:
				if if_yes(config.data['спрашивать_подтверждение_на_замену']) :
					ask_confirmation_to_replacement = True

			if b == False:
				if len(message) == 1:
					print('\n  Внимание!\n\nОшибка в (config.txt):\n  '+message[0]+'\n')
				else:
					print('\n  Внимание!\n\nОшибки в (config.txt):')
					for i in message:
						print('  '+i)
					print()

				inp = input('\nИсправьте и нажмите Enter для продолжения, либо введите нет для выхода:')
				if if_no(inp):
					quit()

				if os.path.isfile(config.path):
					config.load_file()
				else:
					print('Файла config.txt нет, он будет создан с настройками по умолчанию.')
					
					create_config()
		
					break
			else:
				break

		# На всякий случай, чтобы уменьшить вероятность ошибок в программе
		if change_only_meta_information :
			quality = None
			progressive = None
			resize_relative = None
			resize_percent = None
			resize_w = None
			resize_h = None
			resize_difference = None

		#---------------------Начинаем работу-------------------------#

		# выводим конфиг

		print('\nСкрипт будет работать с такой конфигурацией:')

		for i in range( len(list_config) ):
			if not change_only_meta_information :
				if ( ( (list_config[i][0] == 'resize_difference') and resize_difference_Show ) # если resize_difference учитывается, с текущими настройками - выводим его тоже
					or (list_config[i][0] != 'resize_difference') ) :
					print('  '+list_config[i][0]+' = ' + config.data[ list_config[i][0] ])
			else:
				if ( (list_config[i][0] != 'quality')
					and (list_config[i][0] != 'progressive')
					and (list_config[i][0] != 'resize')
					and (list_config[i][0] != 'resize_difference') ) :
					print('  '+list_config[i][0]+' = ' + config.data[ list_config[i][0] ])

		print('\n  Фото будут обрабатываться во всех подпапках директории:\n  ' + path_dir)

		inp = input('\nВведите yes или да чтобы начать обработку фото, либо ничего для отмены:')

		if if_yes(inp) :

			tree = os.walk(path_dir)  # walk возвратил объект-генератор

			# try:
			# 	# удаляем сначала
			# 	if os.path.exists(path_dir+'/'+temp):
			# 		shutil.rmtree(path_dir+'/'+temp, ignore_errors=False, onerror=None)
			# 		time.sleep(1.5) #чтобы операционка успела сообразить
			# except OSError:
			# 	print ("Удалить вспомогательную директорию не удалось!")
			# else:
			# 	try:
			# 		os.mkdir(path_dir+'/'+temp)
			# 	except OSError:
			# 		print ("Создать вспомогательную директорию не удалось! попробуйте ещё раз")
			# 	else:
			print('_____START_____\n')
			# перебираем дерево каталогов и файлов

			b_create_temp_log = False

			time_start = datetime.strftime(datetime.now(), '%Y%m%d_%H%M')

			i_dirs_img = 0 # счётчик папок в которых фото

			temp_log = CfgCreator(path_root+'\\temp.log')

			for root, dirs, files in tree:

				if root.find(path_root) == -1 : # если это не наша временная папка
					# Проверяем очередную папку

					i_img = 0; # счётчик фотографий в папке

					temp_dir_log = CfgCreator(root+'\\temp_dir.log')

					len_max = 0 #запоминаем максимальную длину имени фото, чтобы выравнивать вывод

					changed = False # признак что в этой папке обработан хотябы 1 файл
					changed_restored = False # признак что в этой папке восстановлено фото

					for f in files:

						if (os.path.splitext(f)[1].lower() == '.jpg') :

							if f == jpg_name_temp : # иногда бывает что временный файл jpg_name_temp не успевает переименоваться, и попадает в объект генератор walk()
								if os.path.isfile(root+'\\'+jpg_name_temp):
									print('скрипт уже запускался раньше')
									input()
								continue
							
							if i_img == 0 :
								if b_create_temp_log == False :
									temp_log.push('time', time_start)
									temp_log.push('path', path_root)
									b_create_temp_log = True
									
								print('Поиск '+root)

								temp_log.push(str(i_dirs_img), root+'\\temp_dir.log')

								i_dirs_img += 1;

							if len(f)+1 < len_max :
								print(' '+f, end = ' '*(len_max - len(f)))
							else:
								print(' '+f, end = ' ')
								if len(f)+1 > len_max :
									len_max = len(f)+1


							time_sec = os.path.getmtime(root + '\\' + f)  # получаем время изменения файла
							# time_sec_reed_Exif = False


							# Если возможно считываем Exif
							try:
								img = Image.open(root + '\\' + f)
								Image_open = True
							except IOError:
								Image_open = False

							exif_exists = False
							preview_exists = False
							get_exif = img.info.get('exif')

							if Image_open :
								if get_exif == None :
									print(' нет Exif ', end = '')
								else:
									exif_exists = True

									# Есть ли превью
									os.chdir(root)
									cmd = path_root[:3]+'"'+path_root[3:]+'"\\lib\\exiftool -ifd1:all ".\\'+f+'"'
									PIPE = subprocess.PIPE
									p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT)
									out = str(p.stdout.read())
									find_ok = re.findall(r'\\nThumbnail Image', out)
									if find_ok :
										preview_exists = True
										print(' содержит Exif(с превью) ', end = '')
									else:
										print(' содержит Exif(без превью) ', end = '')
									os.chdir(path_root)

									

									# Разные фотоаппараты по разному ставят эти теги, но в большинстве присутствуют DateTimeOriginal, DateTimeDigitized, DateTime
									exif_date = {}
									info = img._getexif()
									for tag, value in info.items():
										# decoded = TAGS.get(tag, tag) # from PIL.ExifTags import TAGS
										if tag == 36867: # DateTimeOriginal
											exif_date['DateTimeOriginal'] = value
										elif tag == 36868 : # DateTimeDigitized
											exif_date['DateTimeDigitized'] = value
										elif tag == 306: # DateTime
											exif_date['DateTime'] = value
										elif tag == 25986 : # SubSecDateTimeOriginal
											exif_date['SubSecDateTimeOriginal'] = value
										elif tag == 44089 : # CreateDate
											exif_date['CreateDate'] = value
										elif tag == 69336 : # ModifyDate
											exif_date['ModifyDate'] = value
										elif tag == 7905 : # GPSDateStamp
											exif_date['GPSDateStamp'] = value
									# '2018:05:10 19:34:17'
									date = None
									if 'DateTimeOriginal' in exif_date : # в AnalogExif написано что это Original Capture Time
										find = re.findall('([\d][\d][\d][\d]):([\d][\d]):([\d][\d])[ \t]+([\d][\d]):([\d][\d]):([\d][\d])', exif_date['DateTimeOriginal'], flags=re.ASCII)
										if find :
											date = find[0]
									if date == None :
										if 'DateTimeDigitized' in exif_date :
											find = re.findall('([\d][\d][\d][\d]):([\d][\d]):([\d][\d])[ \t]+([\d][\d]):([\d][\d]):([\d][\d])', exif_date['DateTimeDigitized'], flags=re.ASCII)
											if find :
												date = find[0]
									if date == None :
										if 'DateTime' in exif_date :
											find = re.findall('([\d][\d][\d][\d]):([\d][\d]):([\d][\d])[ \t]+([\d][\d]):([\d][\d]):([\d][\d])', exif_date['DateTime'], flags=re.ASCII)
											if find :
												date = find[0]
									if date == '' :
										if 'SubSecDateTimeOriginal' in exif_date :
											find = re.findall('([\d][\d][\d][\d]):([\d][\d]):([\d][\d])[ \t]+([\d][\d]):([\d][\d]):([\d][\d])', exif_date['SubSecDateTimeOriginal'], flags=re.ASCII)
											if find :
												date = find[0]
									if date == None :
										if 'CreateDate' in exif_date :
											find = re.findall('([\d][\d][\d][\d]):([\d][\d]):([\d][\d])[ \t]+([\d][\d]):([\d][\d]):([\d][\d])', exif_date['CreateDate'], flags=re.ASCII)
											if find :
												date = find[0]
									if date == None :
										if 'ModifyDate' in exif_date :
											find = re.findall('([\d][\d][\d][\d]):([\d][\d]):([\d][\d])[ \t]+([\d][\d]):([\d][\d]):([\d][\d])', exif_date['ModifyDate'], flags=re.ASCII)
											if find :
												date = find[0]
									if date == None :
										if 'GPSDateStamp' in exif_date :
											find = re.findall('([\d][\d][\d][\d]):([\d][\d]):([\d][\d])[ \t]+([\d][\d]):([\d][\d]):([\d][\d])', exif_date['GPSDateStamp'], flags=re.ASCII)
											if find :
												date = find[0]

									if date != None :
										datetime_object = datetime.strptime(date[0]+date[1]+date[2]+date[3]+date[4]+date[5], '%Y%m%d%H%M%S')				
										 # print(datetime.strftime(datetime_object, '%Y%m%d_%H%M%S'))
										time_sec = time.mktime(datetime_object.timetuple())

							# print( print(time.ctime(time_sec)) )


							# определяем повреждено ли фото
							# определяем с помощю jpgtest(простецкая оболочка libjpeg написанная неким персонажем с форума http://forum.ixbt.com/topic.cgi?id=23:28361:274#274)
							# Можно определить поймав исключение от метода img.load(), но у jpgtest более подробное сообщение об ошибке и быстрее работает.
							# Есть ещё jpginfo, но слишком долго работает.
							cmd = r'.\lib\jpgtest "'+root + '\\' + f+'"'
							PIPE = subprocess.PIPE
							p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT)  # выполняем команду в ОС
							out = p.stdout.read()
							if out != b'OK\r\n':
								out = str(out)[1:].replace('\\r', '').replace('\\n', '\n     ').replace('\\t', '')
								print('\n   libjpeg:'+out)
								# восстанавливаем превью
								if damaged_photos :
									def final(prefix_thumbnail, changed_restored):
										if os.path.isfile(os.path.splitext(f)[0] + prefix_thumbnail) :
											print('   '+os.path.splitext(f)[0] + prefix_thumbnail, end=' ')
											# переносим Exif с фото на миниатюру если получится
											if exif_exists :
												cmd = path_root[:3]+'"'+path_root[3:]+'"\\lib\\exiftool -overwrite_original -TagsFromFile "'+f+'" -all:all ".\\'+os.path.splitext(f)[0] + prefix_thumbnail+'"'
												PIPE = subprocess.PIPE
												p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT)
												out = str(p.stdout.read())
												find_ok = re.findall('1 image files updated', out)
												if find_ok :
													print(' copy Exif ', end='')
											# 
											if time_modified :
												os.utime(os.path.splitext(f)[0] + prefix_thumbnail, (time_sec, time_sec))
												print(' date time restore ', end='')
											print(' ок')
											changed_restored = True
											temp_dir_log.push(str(i_img), '*+'+root+'\\'+f) # значит - успешно всё выполнили
										else:
											print('   Странно, не удаётся найти файл миниатюры!')
										return changed_restored

									os.chdir(root)
									temp_dir_log.push(str(i_img), '*'+root+'\\'+f) # значит - начинаем переименовывать файл оригинала и создавать миниатюры
									cmd = path_root[:3]+'"'+path_root[3:]+'"\\lib\\exiftool -a -b -W %d%f_%t%-c.%s -preview:all ".\\'+f+'"'
									PIPE = subprocess.PIPE
									p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT)
									out = str(p.stdout.read())
									out = out[1:].replace('\\r', '').replace('\\n', '\n     ').replace('\\t', '')

									# смотрим имя файла - если оно содержит русские буквы и недопустимые символы, ExifTool в лог крякозябли выдаёт - исправляем лог
									if re.match(r'^[^А-Яа-яёЁ\|/:*?<>"]+$', f) == None :
										if 'FileName encoding not specified' in out : # дополнительная проверка
											out = re.sub('Warning: FileName encoding not specified - ./[^/]*.[jJ][pP][gG][\n] {5}', '', out)
											out = re.sub('./[^/]*.[jJ][pP][gG]', './'+f, out)

									print('   ExifTool:'+out)

									thumbnail_n = re.findall('(\d) output files created', out)
									if thumbnail_n :
										thumbnail_n = int(thumbnail_n[0])
										if thumbnail_n == 0 :
											print('   Фото повреждено, извлечь миниатюру не удалось(:')
										elif thumbnail_n == 1:
											print('   Фото повреждено, удалось извлечь миниатюру:')
											changed_restored = final('_ThumbnailImage.jpg', changed_restored)
										elif thumbnail_n > 1:
											print('   Фото повреждено, удалось извлечь миниатюры:')
											changed_restored = final('_ThumbnailImage.jpg', changed_restored)
											for t_n in range(2, thumbnail_n) :
												changed_restored = final('_ThumbnailImage-'+str(t_n-1)+'.jpg', changed_restored)
									else:
										print('   фото повреждено, извлечь миниатюру не удалось(:')

									# смотрим имя файла - если оно содержит русские буквы и недопустимые символы - переименовываем(разделил чтобы лишний раз не переименовывать оригинал)
									# if re.match(r'^[^А-Яа-яёЁ\|\/:*?<>"]+$', f) == None : # файл с нечитаемым для ExifTool именем
									# 	os.rename(f, jpg_name_temp)
									# 	cmd = path_root[:3]+'"'+path_root[3:]+'"\\lib\\exiftool -a -b -W %d%f_%t%-c.%s -preview:all ".\\'+jpg_name_temp+'"'
									# 	PIPE = subprocess.PIPE
									# 	p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT)
									# 	out = p.stdout.read()
									# 	os.rename(jpg_name_temp, f)
									# 	out = str(out).replace(jpg_name_temp, f)
									# 	out_resault(out, os.path.splitext(jpg_name_temp)[0])
									# else:

									# 	out_resault(str(out))  # не передаём имя файла, потому что не нужно менять имя миниатюры

									os.chdir(path_root)

								i_img += 1;
								if Image_open:
									img.close()
								continue
							# 

							progressive_f = False
							mess_progressive = ''

							resize_img = False
							w = 0
							h = 0

							if not change_only_meta_information :

								if (progressive == 2) or not change_only_meta_information :  # оставить как было
									if img.info.get('progression') == 1 :
										progressive_f = True
										print(' progressive ', end='')
									else:
										print(' baseline ', end='')
								else:
									if progressive == 1 :
										progressive_f = True
										if img.info.get('progression') == 1 :
											print(' progressive ', end='')
										else:
											mess_progressive = ' baseline->progressive '
									if progressive == 0 :
										if img.info.get('progression') == 1 :
											mess_progressive = ' progressive->baseline '
										else:
											print(' baseline ', end='')

								if resize_relative :
									if resize_percent < 100 :
										w = int( round( img.size[0]*resize_percent/100) )
										h = int( round( img.size[1]*resize_percent/100) )
										if ( (img.size[0] - w) < resize_difference ) and ( (img.size[1] - h) < resize_difference ) :
											w = img.size[0]
											h = img.size[1]
										else:
											resize_img = True
								else:
									if ( (img.size[0] - resize_w) >= resize_difference ) or ( (img.size[1] - resize_h) >= resize_difference ) :
										resize_img = True
										w = resize_w
										h = resize_h

								if resize_img :
									temp_wh = img.size
									img.thumbnail(size=(w,h), resample=Image.LANCZOS)
									print(' w:'+str(temp_wh[0])+'->'+str(img.size[0]) + ' h:'+str(temp_wh[1])+'->'+str(img.size[1]), end = ' ')


							if exif_exists == False :

								if not change_only_meta_information :
									temp_dir_log.push(str(i_img), root+'\\'+f) # значит - начинаем сохранять изменённый файл
									img.save(root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], 'JPEG', 
										quality=quality,
										optimize=True,
										progressive=progressive_f )
									print(mess_progressive, end='')
									if time_modified :
										os.utime(root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], (time_sec, time_sec))
										print(' date time restore ', end='')
									temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
									print(' ок', end = '')
									changed = True
								else:
									if time_modified :
										temp_dir_log.push(str(i_img), root+'\\'+f) # значит - начинаем сохранять изменённый файл
										shutil.copyfile(root + '\\' + f, root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1])
										os.utime(root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], (time_sec, time_sec))
										print(' date time restore ', end='')
										temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
										print(' ок', end = '')
										changed = True

								print()
							else:
								
								if not change_only_meta_information :
									if remove_exif :
										if remove_preview or ( (remove_preview == False) and (preview_exists == False) ) :
											temp_dir_log.push(str(i_img), root+'\\'+f)  # значит - начинаем сохранять изменённый файл
											img.save(root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], 'JPEG', 
												quality=quality,
												optimize=True,
												progressive=progressive_f )
											print(mess_progressive+' Exif удалено ', end='')
											if time_modified :
												os.utime(root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], (time_sec, time_sec))
												print(' date time restore ', end='')
											temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
											print(' ок')
											changed = True
										else:
											temp_dir_log.push(str(i_img), root+'\\'+f) # значит - начинаем сохранять изменённый файл
											img.save(root+'\\'+jpg_name_temp, 'JPEG', 
												quality=quality,
												optimize=True,
												progressive=progressive_f,
												exif=get_exif )
											print(mess_progressive, end='')
											cmd = '-overwrite_original -all= -tagsfromfile @ -ifd1:all ".\\'+jpg_name_temp+'"'
											cmd_exiftool(root, cmd, os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], ' Exif удалено(кроме превью) ', time_modified, time_sec, changed)
											temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
											changed = True
									else:
										if remove_preview and preview_exists :
											temp_dir_log.push(str(i_img), root+'\\'+f) # значит - начинаем сохранять изменённый файл
											img.save(root+'\\'+jpg_name_temp, 'JPEG', 
												quality=quality,
												optimize=True,
												progressive=progressive_f,
												exif=get_exif,
												icc_profile=img.info.get('icc_profile'))
											print(mess_progressive, end='')
											# удаляем привью с помощю ExifTool
											# cmd = r'.\lib\exiftool -a -b -W %d%f_%t%-c.%s -preview:all ".\temp\\1.jpg"'
											# cmd = r".\lib\exiftool -tagsFromFile 1.jpg -XMP:All= -ThumbnailImage= -m 2.jpg"
											# cmd = r".\lib\exiftool -a -b -W %d%f_%t%-c.%s -preview:all 2.jpg"
											# cmd = r".\lib\exiftool -thumbnailimage= 2.jpg"
											# cmd = r".\lib\exiftool -ifd1:all= -ext jpg 2.jpg"
											# cmd = r".\lib\exiftool -previewimage= 2.jpg"
											# cmd = r'.\lib\exiftool -overwrite_original -all= -tagsfromfile @ -ifd1:all ".\temp\1.jpg"'
											cmd = '-overwrite_original -ifd1:all= ".\\'+jpg_name_temp+'"'
											cmd_exiftool(root, cmd, os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], ' превью удалено ', time_modified, time_sec, changed)
											temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
											changed = True
										else:
											temp_dir_log.push(str(i_img), root+'\\'+f) # значит - начинаем сохранять изменённый файл
											img.save(root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], 'JPEG', 
												quality=quality,
												optimize=True,
												progressive=progressive_f,
												exif=get_exif,
												icc_profile=img.info.get('icc_profile'))
											print(mess_progressive, end='')
											if time_modified :
												os.utime(root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], (time_sec, time_sec))
												print(' date time restore ', end='')
											temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
											print(' ок')
											changed = True
								else:
									if remove_exif :
										if remove_preview or ( (remove_preview == False) and (preview_exists == False) ) :
											temp_dir_log.push(str(i_img), root+'\\'+f)  # значит - начинаем сохранять изменённый файл
											shutil.copyfile(root + '\\' + f, root+'\\'+jpg_name_temp)
											cmd = '-overwrite_original -all= ".\\'+jpg_name_temp+'"'
											changed = cmd_exiftool(root, cmd, os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], ' Exif удалено ', time_modified, time_sec, changed)
											temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
										else:
											temp_dir_log.push(str(i_img), root+'\\'+f) # значит - начинаем сохранять изменённый файл
											shutil.copyfile(root + '\\' + f, root+'\\'+jpg_name_temp)
											cmd = '-overwrite_original -all= -tagsfromfile @ -ifd1:all ".\\'+jpg_name_temp+'"'
											changed = cmd_exiftool(root, cmd, os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], ' Exif удалено(кроме превью) ', time_modified, time_sec, changed)
											temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
									else:
										if remove_preview and preview_exists :
											temp_dir_log.push(str(i_img), root+'\\'+f) # значит - начинаем сохранять изменённый файл
											shutil.copyfile(root + '\\' + f, root+'\\'+jpg_name_temp)
											cmd = '-overwrite_original -ifd1:all= ".\\'+jpg_name_temp+'"'
											changed = cmd_exiftool(root, cmd, os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], ' превью удалено ', time_modified, time_sec, changed)
											temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
										else:
											if time_modified :
												temp_dir_log.push(str(i_img), root+'\\'+f) # значит - начинаем сохранять изменённый файл
												shutil.copyfile(root + '\\' + f, root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1])
												os.utime(root+'\\'+os.path.splitext(f)[0]+'__b'+os.path.splitext(f)[1], (time_sec, time_sec))
												print(' date time restore ', end='')
												temp_dir_log.push(str(i_img), '+'+root+'\\'+f) # значит - успешно сохранили
												print(' ок', end='')
												changed = True
											print()
							img.close()

							i_img += 1;


					if ask_confirmation_to_replacement and (i_img > 0) :
						if changed or changed_restored :
							if changed :
								print(' В текущей папке обработка завершена.')
								print('  Введите yes или да - чтобы скрипт заменил оригиналы обработанными фото.')
								print('  Введите no или нет - чтобы скрипт оставил копии фото в этой папке.')
								print('  Введите s или п - чтобы пропустить, обработанные фото будут удалены.')
								while True :
									inp = input('Введите да, нет или s и нажмите Enter:')
									if if_yes(inp) :
										# удаляем оригиналы, копии переименовываем, удаляем файл логов

										break
									elif if_no(inp) :
										# удаляем файл логов

										break
									elif (inp.lower() == 's') or (inp.lower() == 'п') :
										# удаляем обработанные файлы
										for i in temp_dir_log.data :
											if temp_dir_log.data[i][0] == '+' :
												if os.path.isfile( os.path.splitext( temp_dir_log.data[i][1:] )[0]+'__b.jpg' ) :
													os.remove( os.path.splitext( temp_dir_log.data[i][1:] )[0]+'__b.jpg' )
											
										break

							if changed_restored :
								print(' В текущей папке извлечены миниатюры из повреждённых фото.')
								print('  Введите yes или да - чтобы скрипт оставил миниатюры.')
								print('  Введите no или нет - чтобы скрипт удалил миниатюры.')
								if input_yes_no() :
									# оставляем миниатюры

									pass
								else:
									# удаляем миниатюры
									for i in temp_dir_log.data :
										if temp_dir_log.data[i][0] == '*' :
											if temp_dir_log.data[i][1] == '+' :
												if os.path.isfile( os.path.splitext( temp_dir_log.data[i][2:] )[0]+'_ThumbnailImage.jpg' ) :
														os.remove( os.path.splitext( temp_dir_log.data[i][2:] )[0]+'_ThumbnailImage.jpg' )

							if os.path.isfile( temp_log.data[str(i_dirs_img-1)] ) :
								os.remove( temp_log.data[str(i_dirs_img-1)] )

						else:
							print(' В текущей папке ни одно фото не обработано.')
							input('Нажмите Enter для продолжения:')


		
			if os.path.exists(path_root+'\\temp'):
				shutil.rmtree(path_root+'\\temp', ignore_errors=False, onerror=None)
				# time.sleep(1.5) #чтобы операционка успела сообразить

			temp_log.delete_file()

			print('___COMPLETED___\n\n')


if __name__ == '__main__':
	main()
