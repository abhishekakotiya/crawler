# crawler
a simple web crawler written in python

required: Python 3.x and BeautifulSoup4  

### About
* creates an index of keywords based on html content from the crawled urls.  
* uses RobotParser to ignore pages which are not supposed to be crawled.  
* ranking algorithm to rank pages for ordered search and finding the best result  
* for keyword lookup matches substrings in index keys as well to return url results using re.match  

### Steps to run:    
1. open crawler.py in a text editor  
2. add url(s) in seed_pages variable  
3. add keyword in keyword variable  
4. python crawler.py
