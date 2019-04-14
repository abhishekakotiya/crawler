#an index is maintained with a set of keywords and their their related urls
#the data structure of the index is a dictionary with a key(keyword), value(list of urls) pair:
#index = {key : (url1, url2, ...), key : (url1, url2, ...), ...}
#structure for graph is as follows:
#graph = {url: [url, url, ...]}
#		 page   pages that link to target

from urllib.request import urlopen
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser
from urllib.parse import urlparse, urljoin
import pprint
import re

#to get html content from a url.
def get_page(url):
	#page_url = urlparse(url)
	#base = page_url[0] + '://' + page_url[1]
	robots_url = url + '/robots.txt'
	rp = robotparser.RobotFileParser()
	rp.set_url(robots_url)
	rp.read()
	if not rp.can_fetch('*', url):
		return BeautifulSoup("", "html.parser"), ""
	if url in cache:
		return cache[url], url
	else:
		try:
			content = urlopen(url).read().decode('utf-8')
			return BeautifulSoup(content, "html.parser"), url
		except:
			return BeautifulSoup("", "html.parser"), ""

#adding the keywords and urls on a page to the index
#here content is the content of the page on the given url
def add_page_to_index(index, url, soup):
	#store all the words on the page in a list using split function
	#split function is not useful in case the content has punctuation 
	#marks and other symbols. Therefore, need to find a better way to do it.
	
	try:
		for script in soup(["script", "style"]):
			#remove javascript
			script.decompose() 
		text = soup.get_text()
		# break into lines and remove leading and trailing space on each
		lines = (line.strip() for line in text.splitlines())
		# break multi-headlines into a line each
		chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
		# drop blank lines
		text = '\n'.join(chunk for chunk in chunks if chunk)
	except:
		return
	keywords = text.split()
	for keyword in keywords:
		add_to_index(index, keyword, url)

#query or lookup all the urls for some keyword
def lookup(index, keyword):
	match_str = '.*'+keyword+'+.*'
	index_str = list(index.keys())
	results = []
	for i in range(len(index_str)):
		if re.match(match_str, index_str[i], re.IGNORECASE):
			results.extend(index[index_str[i]])
	
	return results

#add the keyword and url to the index
def add_to_index(index, keyword, url):
		
	#if keyword found in the index, then add the url to 
	#the list of urls for that keyword
	if keyword in index:
		index[keyword].add(url)
	else:		
		#if keyword is not found, then add a new entry of keyword and 
		#it's associated url to the index 
		index[keyword] = set([url])

"""
#get next url starting from the given page
def get_next_target(page):

	#the first href attribute encountered on the page
	start_link = page.find('<a href=')
	
	#if no href attribute, then no link
	if start_link == -1:
		return None, 0
	
	start_quote = page.find('"', start_link) 
	end_quote = page.find('"', start_quote+1)
	
	#url from first " to second " encountered
	url = page[start_quote+1:end_quote]
	
	return url, end_quote
"""

#get all the links on the page
def get_all_links(page, url):
	
	links = []
	#page_url = urlparse(url)

	"""
	if page_url[0]:
		base = page_url[0] + '://' + page_url[1]
		robots_url = urljoin(base, '/robots.txt')
	else:
		robots_url = "http://www.udacity-forums.com/robots.txt"
	"""

	robots_url = url + '/robots.txt'
	rp = robotparser.RobotFileParser()
	rp.set_url(robots_url)
	
	try:
		rp.read()
	except:
		pass
	#print rp
	
	for link in page.find_all('a'):
		link_url = link.get('href')
		#Ignore links that are 'None'.
		if link_url == None: 
			pass
		elif not rp.can_fetch('*', link_url):
			pass		
		#Ignore links that are internal page anchors. 
		#Urlparse considers internal anchors 'fragment identifiers', at index 5. 
		elif urlparse(link_url)[5] and not urlparse(link_url)[2]: 
			pass
		elif urlparse(link_url)[1]:
			links.append(link_url)
		else:
			newlink = urljoin(url, link_url)
			links.append(newlink)
	return links

"""
	while True:
		url, endpos = get_next_target(page)
		
		if url:
			links.append(url)
			page = page[endpos:]
		#if the returned url is None 
		else:
			break
	
	return links
"""

def add_new_links(tocrawl, outlinks, depth):
	for link in outlinks:
		if link:
			if link not in tocrawl:
				#link = str(link)
				tocrawl.append([link, depth+1])	


"""
#union of two lists. All list elements are unique.
def union(p, q):
	for e in q:
		if e not in p:
			p.append(e)
"""

#main method with the seed page as input
def crawl_web(seed, max_pages, max_depth):

	tocrawl = [] #list of pages to be crawled
	for url in seed:
		tocrawl.append([url, 0])  #for multiple seed pages

	crawled = [] #list of pages already crawled
	index = {} #initially the dictionary must be empty
	graph = {} #for ranking pages.

	while tocrawl:
		page, depth = tocrawl.pop(0)

		if page not in crawled and len(crawled) < max_pages and depth <= max_depth:
			soup, url = get_page(page) #get the content from the url
			cache[url] = soup
			add_page_to_index(index, page, soup)
			outlinks = get_all_links(soup, url)
			graph[page] = outlinks
			add_new_links(tocrawl, outlinks, depth)
			#union(tocrawl, get_all_links(content))			
			crawled.append(page)
	
	return index, graph
	#return crawled, graph

def compute_ranks(graph):
	d = 0.8 #damping factor
	numloops = 10 #number of times we go through relaxation. It's value affects the accuracy of the algorithm

	ranks = {}
	npages = len(graph) #number of nodes of the graph.

	for page in graph:
		ranks[page] = 1.0 / npages

	for i in range(0, numloops):
		newranks = {}

		for page in graph:
			newrank = (1 - d) / npages
			for node in graph:
				if page in graph[node]:
					newrank += d * ranks[node] / len(graph[node])

			newranks[page] = newrank
		ranks = newranks

	return ranks 

#returns the one URL most likely to be the best site for that keyword
def lucky_search(index, ranks, keyword):
	urls = lookup(index, keyword)
	if not urls:
		return None
	urls = list(urls)
	best_page = urls[0]
	for candidate in urls:
		if ranks[candidate] > ranks[best_page]:
			best_page = candidate
	return best_page

	
#returns sorted ordered list according to page ranks of urls with matching keyword
def ordered_search(index, ranks, keyword):
	pages = lookup(index, keyword)
	if not pages:
		return None
	return quicksort(list(pages), ranks)

#quicksort algorithm
def quicksort(pages, ranks):
	if len(pages) <= 1:
		return pages
	left = [x for x in pages[1:] if ranks[x] > ranks[pages[0]]]
	right = [x for x in pages[1:] if ranks[x] <= ranks[pages[0]]]
	return quicksort(left, ranks) + [pages[0]] + quicksort(right, ranks)


"""
#craw_web with max depth as second parameter
def crawl_web(seed, max_depth):
	tocrawl = [seed]
	crawled = []
	next_depth = []
	depth = 0
	while tocrawl and depth <= max_depth:
		page = tocrawl.pop()
		if page not in crawled:
			union(next_depth, get_all_links(get_page(page)))
			crawled.append(page)
		if not tocrawl:
			tocrawl, next_depth = next_depth, []
			depth += 1
	return crawled
"""

"""
	The formula for our ranking algorithm is:
	rank(0, url) = 1 / npages
	newranks[url] = (1 - d) / npages + Summation(p belongs to url) d * rank / number of outlinks from p

	Here, t is timestamp which is used as the terminating case for our recursive definition.
	d = 0.8 is damping constant. It is used to rank pages which has less number of pages but are still more popular.
"""

cache = {}
max_pages = 5
max_depth = 5
# enter valid url(s)
seed_pages = ['url']
# enter keyword to search
keyword = "keyword"

def start_crawl():
	index, graph = crawl_web(seed_pages, max_pages, max_depth)
	# print ("Graph:")
	# print ("\n")
	# pprint.pprint(graph)
	# print ("\n ______________________________________ \n")
	# print ("Index:")
	# print ("\n\n")
	# pprint.pprint(index)
	# print ("\n ______________________________________ \n")
	ranks = compute_ranks(graph)
	print ("\n")
	print ("Ranks:")
	pprint.pprint(ranks)
	print ("\n ______________________________________ \n")
	print ("Search for keyword: " + keyword)
	print ("\n\n")
	results = ordered_search(index, ranks, keyword)
	if results:
		print(*set(results), sep="\n")
	else:
		print (None)
	print ("\n ______________________________________ \n")
	print ("Lucky search for keyword: "+keyword)
	print (lucky_search(index, ranks, keyword))

if __name__ == "__main__":
	start_crawl()