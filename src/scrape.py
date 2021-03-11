import os
import datetime
import csv
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
from stop_words import get_stop_words

saved_domains = {
	"tim.blog":{
		"tag":"div",
		"class": "content-area",
		"regex": r"^/(?P<year>\d+){4}/(?P<month>\d+){2}/(?P<day>\d+){2}/(?P<slug>[\w-]+)/$"
		},
	"a-blog-of-interest.com": {
		"tag": "div",
		"class": "main-container",
		"regex": r"^/blog/(?P<slug>[\w-]+)/$"
		},
	"www.nosolosig.com": {
		"tag": "div",
		"class": "t3-content",
		"regex": r"^/libros-geo/(?P<slug>[\w-]+)$"
		}
	}

def create_csv_path(csv_path):
	if not os.path.exists(csv_path):
		with open(csv_path, 'w') as csvfile:
			header_columns = ['word', 'count', 'timestamp']
			writer = csv.DictWriter(csvfile, fieldnames=header_columns)
			writer.writeheader()

def clean_word(word):
	word = word.replace("!", " ")
	word = word.replace("?", " ")
	word = word.replace(".", " ")
	word = word.replace(",", " ")
	word = word.replace(":", " ")
	word = word.replace(";", " ")
	word = word.replace("(", " ")
	word = word.replace(")", " ")
	word = word.replace("-", " ")
	word = word.replace("--", " ")
	word = word.replace("—", " ")
	word = word.replace("it’s", " ")
	word = word.strip()
	word = word.strip('#')
	word = word.strip('«')
	word = word.strip('»')
	return word

def clean_up_words(words):
	new_words = []
	pkg_stop_words = get_stop_words('en') #language: en, es
	my_stop_words = [" ", 'reply', 'like', 'share', 'tweet','says', 'comments', "i'm", "it's", "you're", "we're" '|', "don't", 'comment', 'buy', 
					 'contact', 'open', 'google', 'maps' , 'positive', 'feedback', 'email',
					'hi', '-', 'etc', 'twitter', 'libro', 'libros', 'tig', 'página', 'páginas', 'páginas ', 'anterior', 'siguiente', 
					'ficha', 'empty', 'nº', '2021', '2020', '2019', '2018',  '2017', '2016',
					 '2015', '2014',  '2013', '2012',  '2011', '2010', 'octubre', '16', 'gratis', 'correo', 'electrónico', 'nosolosig',
					 'autor/a', 'editorial', 'país', 'fecha', 'edición', 'precio', 'isbn', 'idioma',
					 'autor/a ', 'editorial ', 'país ', 'fecha ', 'edición ', 'precio ', 'isbn ', 'idioma ', 'euros', 'español', 'españa']
	for word in words:
		word = word.lower()
		cleaned_word = clean_word(word)
		if cleaned_word in my_stop_words or cleaned_word in pkg_stop_words:
			pass
		else:
			new_words.append(cleaned_word)
	return new_words

def fetch_url(url):
	'''
	Requests package
	'''
	response = requests.Response()
	try:
		response = requests.get(url)
	except requests.exceptions.ConnectionError:
		print("No connection to the url. Please try another one.")
	return response

def validate_url(url):
	http_regex = r'^https?://'
	pattern = re.compile(http_regex)
	is_a_match = pattern.match(url)
	if is_a_match is None:
		raise ValueError("This url does not start with http:// or https://")
	return url

def append_http(url):
	if not url.startswith("http"):
		return f'http://{url}'
	return url

def end_program():
	raise KeyboardInterrupt("Program forced to quit.")

def get_input():
	url = input("What is your url? ")
	if url == "q":
		return end_program()
	url = append_http(url)
	try:
		validate_url(url)
	except ValueError as e:
		print(e)
		print("type 'q' to quit")
		return get_input()
	return url

def get_html_soup(html):
	soup = BeautifulSoup(html, 'html.parser')
	return soup

def get_domain_name(url):
	return urlparse(url).netloc

def get_path_name(url):
	return urlparse(url).path

def get_url_lookup_class(url):
	domain_name = get_domain_name(url)
	lookup_class = {}
	if domain_name in saved_domains:
		'''
		To do: change this to use a CSV file with domains and classes
		'''
		lookup_class = saved_domains[domain_name]
	return lookup_class

def get_content_data(soup, url):
	'''
	Get all html content within the specific tag and class (as "content filters")
	if it is a saved domain, if not get content from the body html tag.
	'''
	lookup_dict = get_url_lookup_class(url) 
	if lookup_dict is None or "tag" not in lookup_dict:
		return soup.find("body")
	soup_data = soup.find(lookup_dict['tag'], {'class': lookup_dict['class']})
	return soup_data
	
def parse_links(soup):
	links = []
	try:
		a_tags = soup.find_all("a", href=True)
		for a in a_tags:
			link = a['href']
			links.append(link)
	except ValueError as e:
		print(e)
	return links

def get_local_paths(soup, url):
	links = parse_links(soup) #list of links
	local_paths = []
	domain_name = get_domain_name(url)
	for link in links:
		link_domain = get_domain_name(link)
		if link_domain == domain_name:
			path = get_path_name(link)
			local_paths.append(path)
		elif link.startswith("/"):
			local_paths.append(link)
	return list(set(local_paths)) #discard duplicates and returns a list

def get_regex_pattern(root_domain):
	pattern = r"^/(?P<slug>[\w-]+)/$"
	if root_domain in saved_domains:
		regex = saved_domains[root_domain].get("regex")
		if regex is not None:
			pattern = regex
	return pattern

def match_regex(string, regex):
	pattern = re.compile(regex)
	is_a_match = pattern.match(string)
	if is_a_match is None:
		return False
	return True

def get_regex_local_paths(soup, url):
	'''
	Local paths to scrape based on a regular expresion from the get_regex_pattern method

	:soup -- get_html_soup
	:url  -- local domain url
	returns list of local  paths from the url
	'''
	links = parse_links(soup)
	local_paths = []
	domain_name = get_domain_name(url)
	regex = get_regex_pattern(domain_name)
	for link in links:
		link_domain = get_domain_name(link)
		if link_domain == domain_name:
			path = get_path_name(link)
			is_match = match_regex(path, regex)
			if is_match:
				local_paths.append(path)
		elif link.startswith("/"):
			is_match = match_regex(link, regex)
			if is_match:
				local_paths.append(link)
	return list(set(local_paths))

def parse_blog_post(path, url):
	domain_name = get_domain_name(url)
	lookup_url = f"http://{domain_name}{path}"
	lookup_response = fetch_url(lookup_url)
	if lookup_response.status_code in range(200, 299):
		lookup_soup = get_html_soup(lookup_response.text)
		#a function targeting a more specific html tag/class can be used instead in this case
		lookup_html_soup = get_content_data(lookup_soup, lookup_url)
		words = lookup_html_soup.text.split()
		clean_words = clean_up_words(words)
	return clean_words

def main():
	url = get_input()
	response = fetch_url(url)
	if response.status_code not in range(200, 299):
		print(f"Invalid request, you cannot to view this. Status: {response.status_code}")
		return None
	response_html = response.text
	soup = get_html_soup(response_html)
	html_soup = get_content_data(soup, url)
	paths = get_regex_local_paths(html_soup, url)
	words = []
	for path in paths:
		print(path)
		clean_words = parse_blog_post(path, url)
		words = words + clean_words
	print(Counter(words).most_common(100))

def create_csv_links_path(csv_path):
	if not os.path.exists(csv_path):
		with open(csv_path, 'w') as csvfile:
			header_columns = ['links']
			writer = csv.DictWriter(csvfile, fieldnames=header_columns)
			writer.writeheader()

def save_links_scraped(url, links):
	timestamp = datetime.datetime.now()
	#date = timestamp.strftime("%Y-%m-%d")
	domain_name = get_domain_name(url)
	filename = domain_name.replace(".", "-") + '-scraped-links__' + str(timestamp) + '.csv'
	path = 'csv/' + filename
	create_csv_links_path(path)
	with open(path, 'a') as csvfile:
			header_columns = ['link']
			writer = csv.DictWriter(csvfile, fieldnames=header_columns)
			for link in links:
				writer.writerow({
						"link": link,
						#"timestamp": timestamp
					})

def create_csv_words_path(csv_path):
	if not os.path.exists(csv_path):
		with open(csv_path, 'w') as csvfile:
			header_columns = ['word', 'count']
			writer = csv.DictWriter(csvfile, fieldnames=header_columns)
			writer.writeheader()

def save_final_words(url, words):
	timestamp = datetime.datetime.now()
	domain_name = get_domain_name(url)
	filename = domain_name.replace(".", "-") + '-words__' + str(timestamp) + '.csv'
	path = 'csv/' + filename
	word_counts = Counter(words)
	create_csv_words_path(path)
	with open(path, 'a') as csvfile:
			header_columns = ['word', 'count']
			writer = csv.DictWriter(csvfile, fieldnames=header_columns)
			for word, count in word_counts.items():
				writer.writerow({
						"word": word,
						"count": count
					})

def fetch_links_words(url):
	print(url, "scraping...")
	response 				= fetch_url(url)
	soup 					= get_html_soup(response.text)
	html_soup 				= get_content_data(soup, url)
	local_paths 			= get_regex_local_paths(html_soup, url)
	domain_name 			= get_domain_name(url)
	to_scrape 				= [f"http://{domain_name}{path}" for path in local_paths]
	words 					= []
	if html_soup:
		words 				= html_soup.text.split()
		clean_words 		= clean_up_words(words)
	return set(to_scrape), clean_words

def scrape_links(to_scrape, scrapped, current_depth=0, max_depth=3, words=[]):
	if current_depth <= max_depth:
			new_set_to_scrape = set()
			while to_scrape:
				item = to_scrape.pop()
				if item not in scrapped:
					new_paths, new_words = fetch_links_words(item)
					words += new_words
					new_set_to_scrape = (new_set_to_scrape | new_paths)
				scrapped.add(item)
			current_depth += 1
			return scrape_links(new_set_to_scrape, scrapped, current_depth=current_depth, max_depth=max_depth, words=words)
	return scrapped, words

def main_with_depth():
	#initialize
	url 								= 'https://www.nosolosig.com/libros-geo' #'https://tim.blog' #get_input()
	to_scrape_a, new_words 				= fetch_links_words(url)
	scrapped_a 							= set([url])
	final_scrapped_items, final_words	= scrape_links(to_scrape_a, scrapped_a, current_depth=0, max_depth=1, words=new_words)
	#save data
	save_words 							= save_final_words(url, final_words)
	save_links 							= save_links_scraped(url, final_scrapped_items)
	#print(Counter(final_words).most_common(30))

#main()
main_with_depth()