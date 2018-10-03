from flask import Flask, json, request, render_template
import tweepy, re
from nltk.corpus import stopwords
import string
from collections import Counter

app = Flask(__name__)
# Load our config from an object, or module (config.py)
app.config.from_object('config')

# These config variables come from 'config.py'
auth = tweepy.OAuthHandler(app.config['TWITTER_CONSUMER_KEY'],
                           app.config['TWITTER_CONSUMER_SECRET'])
auth.set_access_token(app.config['TWITTER_ACCESS_TOKEN'],
                      app.config['TWITTER_ACCESS_TOKEN_SECRET'])
api = tweepy.API(auth)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

def get_tweets(username):
	tweets = []
	for t in tweepy.Cursor(api.user_timeline, screen_name=username).items(30):
		tweets.append({'url': re.findall(r"http\S+", t.text),
		    		  'tweet': re.sub(r"http\S+", "", t.text),
		              'created_at': t.created_at, 
		              'username': username,
		              'headshot_url': t.user.profile_image_url
		              })                                                                          
	return tweets

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/search', methods=['POST'])
def showTweets():
    userId = request.form['text']
    if userId == "":
    	userId = "twitter"
    return render_template("search.html", tweets=get_tweets(userId), username=userId)

regex_str = [
    r'<[^>]+>', # HTML tags
    r'(?:@[\w_]+)', # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', # URLs
 
    r'(?:(?:\d+,?)+(?:\.?\d+)?)', # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])", # words with - and '
    r'(?:[\w_]+)', # other words
    r'(?:\S)' # anything else
]
tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE)
def preprocess(s):
	return tokens_re.findall(s)

punctuation = list(string.punctuation)
stop = stopwords.words('english') + punctuation + ['rt', 'via', '…', "’", "“","”", "amp"]

def analyzeTweets(username, items, top):
	count = Counter()
	for tweet in tweepy.Cursor(api.user_timeline, screen_name=username).items(items):
		terms_stop = [term for term in preprocess(tweet.text) if term.lower() not in stop]
		count.update(terms_stop)
	return [{'word': w,
    		  'count': c
              }
           for (w,c) in count.most_common(top)]	

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/analysis', methods=['POST'])
def showAnalysis():
	userId = request.form['user']
	if userId == "":
		userId = "twitter"
	items = request.form['items']
	top = request.form['top']
	if items == "":
		items = 200
	if top == "":
		top = 5
	items = int(items)
	top = int(top)

	if items < 0:
		items = 200
	if top < 0:
		top = 5
	return render_template("analysis.html", words=analyzeTweets(userId, items, top), username=userId, items=items, top=top)