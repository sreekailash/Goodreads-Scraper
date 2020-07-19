#Import the necessary libraries 

import requests
import csv 
from bs4 import BeautifulSoup
import lxml
import re
from tqdm import tqdm
import time

import pandas as pd

#Input the URL of the list that we'd like to scrape
list_url= 'https://www.goodreads.com/list/show/134.Best_Non_Fiction_no_biographies_'


#Initializing an empty Dataframe which is going to store our output
books_df = pd.DataFrame(columns = ['Title', 'Author', 'Description' 
                               ,'Num_ratings', 'Avg_rating', 'Genres_list',
                               'Main_genre', 'Secondary_genre' , 'Num_pages', 'ISBN','Link'])

#Get the list of books along with the URL 

def get_book_list(list_url, num_pages = 10):

	"""
	Fetches the names of the books along with the corresponding link

	Arguments:
	list_url - The URL of the list that we like to extract
	num_pages - The number of pages in the list that we like to extract

	Returns:
	books_dict -- A python dictionary that contains the book title and the link to the book
	"""

	books_dict = {}

	for i in tqdm(range(1,num_pages)):
	    bookpage=str(i)
	    stuff=requests.get(list_url + '?page=' + bookpage)
	    soup = BeautifulSoup(stuff.text, 'html.parser')

	    for e in soup.select('.bookTitle'):
	        books_dict[e.get_text(strip = 'True')] = e['href']

	    time.sleep(2)

	return books_dict


#Get the key corresponding to a value 

def get_key(val, my_dict): 

	"""
	Returns the key corresponding to the input value in the dictionary of interest

	Arguments:
	val - The value that we are looking for in the dictionary
	my_dict - The dictionary in which we are looking for

	Returns:
	key - The key corresponding to the value 

	"""

    for key, value in my_dict.items(): 
         if val == value: 
                return key 
  
    return "key doesn't exist"

#Get the genres that a book falls under

def get_main_genres(d):

	"""
	Gets the list of genres that a book belongs to along with the number of readers who have placed it in a genre, the main genre and the secondary genre
	
	Arguments:
	d - A beautiful soup object which is the result of us parsing the URL of interest

	Returns:
	genre_dict - Has the name of the genre and the number of readers who have placed it there
	Max_genre - The primary genre of the book
	Second_genre - The secondary genre 

	P.S. Forgive the naming convention :P 

	"""
    
    genre_dict = {}
    genres = d.select("div.elementList div.right a")
        
    for g in genres:
        genre_dict[g['href'].partition('=')[2]] = int(re.sub(',','',g.get_text().split()[0]))
        
    if len(genre_dict)>0:
        Max_genre = max(genre_dict, key= lambda x: genre_dict[x]) 
    else:
        Max_genre = None
    
    if len(genre_dict)>1:
        second_largest_value = list(sorted(genre_dict.values()))[-2]
    else:
        second_largest_value = None
    
    second_genre = get_key(second_largest_value, genre_dict)
        
    return genre_dict, Max_genre, second_genre

#The key function that extracts the necessary book details 

def get_book_details(book_url):

	"""
	Extract the required details (the book attributes that we have included while defining the empty output dataframe) of the book

	Arguments:
	book_url - The goodreads URL of the book 

	Returns: 
	book_dict - Dictionary containing the required attributes of the book 

	"""
    
    book_dict = {}
    
    page=requests.get(book_url)
    soup=BeautifulSoup(page.text, 'html.parser')
    
    title = soup.select("meta[property='og:title']")[0]['content']
    author = soup.find_all('a', class_ = 'authorName')[0].get_text(strip = True)

    desc = soup.find('div', id = 'description')
    if desc is not None:
        try:
            description = desc.find_all('span')[1].get_text()
        except:
            description = desc.find_all('span')[0].get_text()
    else:
        description = None

    if soup.find('meta', itemprop = 'ratingCount') is not None:
        num_ratings = soup.find('meta', itemprop = 'ratingCount')['content']
    else:
        num_ratings = None

    if soup.find('span', itemprop = 'ratingValue') is not None:    
        rating = soup.find('span', itemprop = 'ratingValue').get_text(strip = 'True')
    else:
        rating = None

    genre_list, main_genre, secondary_genre = get_main_genres(soup)

    if soup.select("meta[property='books:page_count']") is not None and len(soup.select("meta[property='books:page_count']")) != 0: 
        num_pages = soup.select("meta[property='books:page_count']")[0]['content']
    else:
        num_pages = None

    if soup.select("meta[property='books:isbn']") is not None and len(soup.select("meta[property='books:isbn']")) != 0:
        isbn = soup.select("meta[property='books:isbn']")[0]['content']
    else:
        isbn = None

    book_dict = {
        'Title' : title,
        'Author' : author,
        'Description' : description,
        'Num_ratings' : num_ratings,
        'Avg_rating' : rating,
        'Genres_list' : genre_list,
        'Main_genre' : main_genre,
        'Secondary_genre': secondary_genre,
        'Num_pages' : num_pages,
        'ISBN' : isbn,
        'Link' : book_url
    }
    
    return book_dict

#The main section 

books_dict = {}

books_dict = get_book_list(list_url, num_pages = 3) #Gets the books and the URL

# Looping through the list of books that we want to scrape

for book in tqdm(list(books_dict.values())):  #tqdm helps us track the loop progress 
    
    book_url = 'https://www.goodreads.com/' + str(book)
    print("Extracting from {}".format(book_url))
    books_df = books_df.append(get_book_details(book_url), ignore_index= True)

#Write to CSV 
final_df.to_csv('scraped_books.csv')
