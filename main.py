from multiprocessing import Process, Queue
from PIL import Image
from time import perf_counter
from unidecode import unidecode
import os, json, base64

ROOT_PATH = os.path.dirname(__file__)
NEW_IMGS_PATH = os.path.join(os.path.dirname(__file__), 'new')

def caesar_cipher(text):
	offset = 42
	result = ''
	for char in text:
		if char.isalpha():
			if char.islower():
				result += chr(((ord(char) - ord('a') + offset) % 26) + ord('a'))
			else:
				result += chr(((ord(char) - ord('A') + offset) % 26) + ord('A'))
		else:
			result += char
	return result

def resize_and_hide(filename):
	HEIGHT = 600

	path = os.path.join(NEW_IMGS_PATH, filename)
	raw_img = Image.open(path)

	# replace to url-safe str and convert the rest of the accented characters
	filename = unidecode(filename.replace('.png', '').replace('μ', 'muse').replace('♥', ' '))
	# encode
	filename = base64.b64encode(caesar_cipher(filename).encode()).decode() + '.png'

	# resize
	aspect_ratio = float(raw_img.size[1]) / float(raw_img.size[0])
	height = int(HEIGHT * aspect_ratio)
	resized_img = raw_img.resize((HEIGHT, height))
	unhidden_out_path = os.path.join(ROOT_PATH, 'img', 'unhidden', filename)
	resized_img.save(unhidden_out_path)

	# hide
	rgba_img = resized_img.convert('RGBA')
	width, height = rgba_img.size
	for x in range(width):
		for y in range(height):
			r, g, b, a = rgba_img.getpixel((x, y))
			if a != 0:
				rgba_img.putpixel((x, y), (0, 0, 0, a))
	hidden_out_path = os.path.join(ROOT_PATH, 'img', 'hidden', filename)
	rgba_img.save(hidden_out_path)

def dequeue(queue):
	while not queue.empty():
		filename = queue.get()
		print(f'Processing: {filename}')
		resize_and_hide(filename)

if __name__ == '__main__':
	start = perf_counter()

	with open('names.json', 'r') as json_file:
		output = json.load(json_file)

	queue = Queue()
	for filename in os.listdir(os.path.join(NEW_IMGS_PATH)):
		if '_cn' not in filename and '_bg' not in filename and 'norigging' not in filename and '_Original' not in filename:
			queue.put(filename)

			# process details
			name_separated = unidecode(filename.replace('.png', '').replace('μ', 'muse').replace('♥', ' ')).split('_')
			name = name_separated[0]
			skin_info = name_separated[1]

			for detail in output:
				if detail['filename'] == name:
					if skin_info == 'Retrofit':
						detail['retrofit'] = True
					elif skin_info != 'Default' and skin_info not in detail['skins']:
						detail['skins'].append(skin_info)
					break
			else: # make new entry when no record exists
				entry = {
					'filename': '',
					'skins': [],
					'retrofit': False
				}
				entry['filename'] = name
				output.append(entry)
				continue

	processes = [Process(target=dequeue, args=(queue,)) for _ in range(os.cpu_count())]

	for process in processes:
		process.start()

	for process in processes:
		process.join()

	with open('names.json', 'w') as json_file:
		json.dump(output, json_file)

	print(f'Done. Time took: {round(perf_counter() - start, 2)} seconds.')
