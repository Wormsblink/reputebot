import config
import praw
import time
from datetime import datetime
import os

def bot_login():
        print ("Logging in...")
        r = praw.Reddit(username = config.username,
                        password = config.password,
                        client_id = config.client_id,
                        client_secret = config.client_secret,
                        user_agent = "Expert Identifier v0.1")
        print("Log in successful!")
        print(datetime.now().strftime('%d %b %y %H:%M:%S'))
        return r

from newspaper import Article
import spacy
import orcid
from orcidconfig import client_id as institution_key
from orcidconfig import client_secret as institution_secret

from scholarly import scholarly

def run_bot(r, replied_articles_id):
    
    try:

        api = orcid.PublicAPI(institution_key, institution_secret, sandbox=False)
        search_token = api.get_search_token_from_orcid()

    except:
        api = None

    #print("Running Bot")
    for submission in r.subreddit('wormstest').new(limit = 25):

        if (("expert" in submission.title.lower()) and not submission.author == r.user.me() and not "bot" in submission.author.name and submission.id not in replied_articles_id):

            if not submission.selftext:

                qualifications_check = get_qualification_response(submission.url)

                if qualifications_check != None:

                    reputereply = 'The article title mentions an expert. The article text was scanned and the following names were identified: \n\n' + qualifications_check
                    reputereply = reputereply + "\n\n***\n\n" + "[v0.1](" + "https://github.com/Wormsblink/reputebot" + ") by Worms_sg and running on Raspberry Pi400 | PM wormsbot if bot is down"

                    submission.reply(reputereply)

                    print("Replied to submission " + submission.id + " by " + submission.author.name)
                    replied_articles_id.append(submission.id)
                    with open ("replied_articles.txt", "a") as f:
                            f.write(submission.id + "\n")

    #print("Sleeping for 10 seconds")
    time.sleep(10)

def get_replied_articles():
        if not os.path.isfile("replied_articles.txt"):
                replied_articles_id = []
        else:
                with open("replied_articles.txt", "r") as f:
                        replied_articles_id = f.read()
                        replied_articles_id = replied_articles_id.split("\n")

        return replied_articles_id



def get_people_from_article(article_url):

    article = Article(article_url)
    article.download()
    article.parse()
    newstext = article.text

    if not newstext:
        return()
    else:

        # spacy en_core_web_sm
        # most efficient 
        # spacy en_core_web_trf
        # most accurate

        nlp = spacy.load("en_core_web_lg")
        doc = nlp(newstext)

        people = []

        for entity in doc.ents:
            if (entity.label_ == "PERSON"):
                if(len(entity.text.split())>1):
                    people.append(entity.text)

    return people

def search_orcid_credentials(api, subject_name):

    print('Searching ORCID for "' + subject_name + '"')

    search_results = api.search('"' + subject_name + '"')
    if search_results['num-found'] >0:
        return(search_results['result'][0]['orcid-identifier']['path'])
    else:
        return()

def search_google_scholar_credentials(subject_name):
    
    try:
        print("Searching Google Scholar for " + subject_name)
        search_query = scholarly.search_author(subject_name)
        author = scholarly.fill(next(search_query), sections = ['basics', 'publications'])
        scholar_id = author['scholar_id']
        scholar_affliation = author['affiliation']
        nPublications = str(len(author['publications']))
        nCitedby = str(author['citedby'])

        #hindex = author['hindex']

        Greply = 'Recognied by Google Scholar (ID: ' + scholar_id + '). Affliated with ' + scholar_affliation + '.\n\n Published ' + nPublications + ' Articles. Cited ' + nCitedby + '  times.'

# times.\n\nreliability by hindex (' + str(hindex) + '): '
        return (Greply)
    except:
        return()


def get_qualification_response(url):

    people = get_people_from_article(url)
    people = list(set(people))

    print(people)

    Qual_list = ""
    qualifications = None

    if people != []:

        for person in people:
            
            print(person)

            if not api:
                print("ORCID Api Failed. Skipping ORCID Search")

            else:
                qualifications = search_orcid_credentials(api, person)

            Gqualifications = search_google_scholar_credentials(person)

            if not Gqualifications and not qualifications:
                Qual_list = Qual_list   + person + ": No ORCID or Google Scholar qualifications found\n\n"
            else:
                
                Qual_list = Qual_list + person + ".\n\n"

                if not qualifications:
                
                    Qual_list = Qual_list + Gqualifications  + "\n\n"
                else:
                    Qual_list = Qual_list + "ORCID Found: " + qualifications + "\n\n"
          

            return(Qual_list)

    else:
        return(None)

# Main

api = None

r = bot_login()
while True:
    run_bot(r, get_replied_articles())