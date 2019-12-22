#Importing packages
from bs4 import BeautifulSoup
import requests
import pandas as pd

page = requests.get("https://www.scientias.nl")
soup = BeautifulSoup(page.content, 'html.parser')

# Get all the posts (title and href)
coverpage_news = soup.find_all('h2', class_='post-title')

# The following list will contain all articles
news_contents = []
article_links = []
for i in range(len(coverpage_news)):
    print(i)
    link = coverpage_news[i].find('a')['href']
    print(link)
    article = requests.get(link)
    article_content = article.content
    soup_article = BeautifulSoup(article_content, 'html.parser')
    body = soup_article.find_all('section', class_='post-content')
    x = body[0].find_all('p')

    # Unifying the paragraphs
    list_paragraphs = []
    for p in range(len(x)):
        paragraph = x[p].get_text()
        list_paragraphs.append(paragraph)
        final_article = " ".join(list_paragraphs)

    news_contents.append(final_article)
    article_links.append(link)

# Calling DataFrame constructor after zipping
# both lists, with columns specified
df = pd.DataFrame(list(zip(article_links, news_contents)),
               columns =['Link', 'Content'])

# Only last 6 articles
df = df[:6]

# importing libraries
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize, sent_tokenize

def _create_dictionary_table(text_string) -> dict:
    # removing stop words
    stop_words = set(stopwords.words("dutch"))

    words = word_tokenize(text_string)

    # reducing words to their root form
    stem = PorterStemmer()

    # creating dictionary for the word frequency table
    frequency_table = dict()
    for wd in words:
        wd = stem.stem(wd)
        if wd in stop_words:
            continue
        if wd in frequency_table:
            frequency_table[wd] += 1
        else:
            frequency_table[wd] = 1

    return frequency_table


def _calculate_sentence_scores(sentences, frequency_table) -> dict:
    # algorithm for scoring a sentence by its words
    sentence_weight = dict()

    for sentence in sentences:
        sentence_wordcount = (len(word_tokenize(sentence)))
        sentence_wordcount_without_stop_words = 0
        for word_weight in frequency_table:
            if word_weight in sentence.lower():
                sentence_wordcount_without_stop_words += 1
                if sentence[:13] in sentence_weight:
                    sentence_weight[sentence[:13]] += frequency_table[word_weight]
                else:
                    sentence_weight[sentence[:13]] = frequency_table[word_weight]

        sentence_weight[sentence[:13]] = sentence_weight[sentence[:13]] / sentence_wordcount_without_stop_words

    return sentence_weight


def _calculate_average_score(sentence_weight) -> int:
    # calculating the average score for the sentences
    sum_values = 0
    for entry in sentence_weight:
        sum_values += sentence_weight[entry]

    # getting sentence average value from source text
    average_score = (sum_values / len(sentence_weight))

    return average_score


def _get_article_summary(sentences, sentence_weight, threshold):
    sentence_counter = 0
    article_summary = ''

    for sentence in sentences:
        if sentence[:13] in sentence_weight and sentence_weight[sentence[:13]] >= (threshold):
            article_summary += " " + sentence
            sentence_counter += 1

    # If no sentences are surviving treshol cutoff, still add the most important 2
    if sentence_counter == 0:
        res = dict(sorted([(k, v) for k, v in sentence_weight.items()], key=lambda x: x[1])[-2:])
        for sentence in sentences:
            if sentence[:13] in res:
                article_summary += " " + sentence

    return article_summary


def _run_article_summary(article):
    # creating a dictionary for the word frequency table
    frequency_table = _create_dictionary_table(article)

    # tokenizing the sentences
    sentences = sent_tokenize(article)

    # algorithm for scoring a sentence by its words
    sentence_scores = _calculate_sentence_scores(sentences, frequency_table)

    # getting the threshold
    threshold = _calculate_average_score(sentence_scores)

    # producing the summary
    article_summary = _get_article_summary(sentences, sentence_scores, 1.5 * threshold)

    return article_summary

# Add the summary to df and select the used columns
df['summary'] = [_run_article_summary(article) for article in df.Content]
send_df = df[['Link','summary']]


from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configurations and content
recipients = ['kasperde@hotmail.com']
emaillist = [elem.strip().split(',') for elem in recipients]
msg = MIMEMultipart()
msg['Subject'] = "Scientias summaries"
msg['From'] = 'k.sends.python@gmail.com'

html = """\
<html>
  <head></head>
  <body>
    {0}
  </body>
</html>
""".format(send_df.to_html())

part1 = MIMEText(html, 'html')
msg.attach(part1)

# Sending the email
import smtplib, ssl

port = 465  # For SSL
password = open("C:/Users/kaspe/Documents/python_scripts/article_summarize/ps_gmail_send.txt", "r").read()

# Create a secure SSL context
context = ssl.create_default_context()

with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login(msg['From'], password)
    server.sendmail(msg['From'], emaillist , msg.as_string())