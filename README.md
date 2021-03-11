# Python-Web-Scraping

A web scraper built in python to scrape iteratively all of the local paths of a specified base url that match a regular expression, up to a specified max depth. While scraping, the program saves the scraped links, and all the words found within the html with a counter for each repetition. (**scrape.py**)

##### Some instructions:

1. Specify the base **url** of interest. In `main_with_depth()`function.
2. Indicated the **max_depth**, limiting the number of follows the scraper will take from the initial link, within the domain. In `main_with_depth()` function.
3. Include the domain of interest in the **saved_domains** dictionary, specifying the _html tag and class_ (as "content filters") used to select the content to scrape. Also the *regular expression* to be used to obtain the list of local paths to be scrape that match that regex pattern.
4. Specify the *language of the stop words package* (e.g. en, es). Also *include your own stop words* (my_stop_words list) that will be omitted when saving the text. In `clean_up_word()` function.
5. Check result files in “csv” folder with the scraped content (scrapped links; words and their count.)

###### Python packages required:
* [Requests](https://pypi.org/project/requests/)
* [Beautiful Soup](https://pypi.org/project/beautifulsoup4/)
* [Python Stop Words](https://pypi.org/project/stop-words/)

