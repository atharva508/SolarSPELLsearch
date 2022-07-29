
from flask import Flask
from flask_cors import CORS
from flask import request

app = Flask(__name__)
CORS(app)

"""SPELL CHECK"""
from spellchecker import SpellChecker

checker = SpellChecker()

def corrected_spelling(input):
  search_query = input.split() # splits the input query into a list of words

  new_query = "" # instantiates empty string for the new query
  for word in search_query:
    new_query += " " + checker.correction(word) # adds all of the corrected words to the new_query string

  return new_query.strip() # removes excess whitespace and returns corrected query

"""LEMMATIZER"""

import nltk

from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

# tags the parts of speech to prep for lemmatization
def pos_tagger(nltk_tag):
    if nltk_tag.startswith('J'):
        return wordnet.ADJ
    elif nltk_tag.startswith('V'):
        return wordnet.VERB
    elif nltk_tag.startswith('N'):
        return wordnet.NOUN
    elif nltk_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

def lemmatizer(searchQuery):
  lemmatizer = WordNetLemmatizer()
  pos_tagged = nltk.pos_tag(nltk.word_tokenize(searchQuery))#tags all the words in the search query
  wordnet_tagged = list(map(lambda x: (x[0], pos_tagger(x[1])), pos_tagged))#uses the pos_tag funtion to extract the wordnet tag for lemmatization
  lemmatized_sentence = []
  for word, tag in wordnet_tagged:

      if (tag is None):
        if(word!='the'):
         # if there is no available tag, append the token as is
            lemmatized_sentence.append(word)
      elif(lemmatizer.lemmatize(word, tag)!="be"):
           # else use the tag to lemmatize the token(apart from verbs in "be" form)
          lemmatized_sentence.append(lemmatizer.lemmatize(word, tag))
  #joins all the words in the list to form the updated search query
  #lemmatized_sentence = " OR ".join(lemmatized_sentence)
  return lemmatized_sentence

"""FTS FUNCTION"""

import sqlite3

#takes in the searchString and number of required resources as arguments
def searchQuery(searchString, num_results):
  conn = sqlite3.connect('solarspell.db')
  cur = conn.cursor()
  data = cur.execute('SELECT rowid as id,highlight(content_fts, 0 , \'<mark>\', \'</mark>\') as title,file_name, description, file_size FROM content_fts where content_fts match "{}" order by rank limit {}'.format(searchString,num_results)).fetchall()
  #returns the list of search results
  return data

def completeSearch(searchString):
  search_string = corrected_spelling(searchString.lower()) # corrects spelling of the query
  lemmatized_search_words = lemmatizer(search_string) # makes a list with each lemmatized word
  result = searchQuery(search_string,15)
  #Result consists of the files with the exact metadata words
  if (len(result)<5):
        search_string2 = " OR ".join(lemmatized_search_words)
        #returns some files with either words in case of less results
        result2 = searchQuery(search_string2,(10-len(result)))
        for x in result2 :
            if(x not in result):
                result.append(x)
  jsonResult = json.dumps({'searchString' : searchString,'contentList' :convertDict(result) })
  return jsonResult

import json # searchQuery method should return a json file

#helps in converting the list of results into a Dictionary of the required format
def convertDict(listOfResult):
  keys = ['id', 'title', 'file_name','description', 'file_size']
  listOfDicts = []
  
  for j in range(0,len(listOfResult)):
    jDict = {}
    
    for i in range (0,5):
      jDict.update({keys[i]:str(listOfResult[j][i])})
    listOfDicts.append(jDict)
    
  return listOfDicts

@app.route('/search/',methods=['GET'])
def search():
    return completeSearch(request.args.get('search_string'))
    
if __name__ == '__main__':
    app.run(host='0.0.0.0')
