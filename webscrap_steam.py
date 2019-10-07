# Web scrapping of steam website
# game_name, game_href,
# reviews, developer. release_date

# load libraries
import pandas as pd
from bs4 import BeautifulSoup
import requests
import os
import collections
import re
import numpy as np

path_curr = os.getcwd()
url = 'https://store.steampowered.com/search/'
max_pages = 10

# main function
def main(url, max_pages):
    for page in range(max_pages):
        main_gamelist_by_page(page)

# main_gamelisting function
def main_gamelist_by_page(page):

    # create weblinks, eventlists as LIST
    weblinks= web_scrap(url, page)

    # recent_review, all_review, feature_game, date_lists, developer_lists, weblink_worked, game_lists = extract_game_feature(weblinks)
    df = extract_game_feature(weblinks)
    df.to_csv(path_curr + '/csv_files/game_by_page' + str(page+1).zfill(2) +'.csv', encoding = 'utf-8', index=False)


# collect car websites for each page
def web_scrap(url, page):
    weblist = []
    gamelist = []

    # extract html sources
    full_url = url + '?page='+ str(page+1)
    source_code = requests.get(full_url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, "html.parser")

    # extract link & game_soup
    href_soup = soup.findAll('div', {'id':"search_resultsRows"})
    href_small = href_soup[0].findAll('a')
    gamename_soup = soup.findAll('span', {'class': 'title'})

    # href_link, game_name extract
    for link in range(len(href_small)-1):
        # links extract
        href_unicode = href_small[link].get('href')
        href_tmp = re.compile(r'\?(.*)').search(str(href_unicode))#.encode('ascii', 'ignore')
        href_end = href_tmp.group(0)
        href = href_unicode.replace(href_end, '')
        weblist.append(href)

    # print(eventlist)
    return weblist#, gamelist

def extract_game_feature(weblinks):
    n_game = len(weblinks)
    # create pandas
    column_names = ['game_name', 'link',\
     'recent_review_positivity', 'recent_reivew_nvotes', 'recent_review_percentage',\
      'all_review_positivity', 'all_review_nvotes', 'all_review_percentage',\
      'release_date', 'developer','features']
    n_columns = len(column_names)
    empty_list = (list(np.zeros([1, n_columns])))
    df = pd.DataFrame(empty_list, columns = column_names)

    for game in range(n_game-1):
        print(game)
        url_eachgame = weblinks[game+1]
        webhtml = requests.get(url_eachgame)

        # soup = BeautifulSoup(contents, 'lxml')
        eachsoup = BeautifulSoup(webhtml.text, 'html.parser')#

        review_soup = eachsoup.findAll('div', {'class':'user_reviews'})
        review_soup_s = eachsoup.findAll('div', {'class','user_reviews_summary_row'})
        eachsoup.findAll('div', {'class':"apphub_AppName"})

        # only when bs4 worked
        if len(review_soup_s) >=1:
            # ===== game_name
            name_chunck = eachsoup.findAll('div', {'class':"apphub_AppName"})
            game_name = name_chunck[0].text
            df.loc[game, 'game_name'] = game_name
            # ===== link
            df.loc[game, 'link'] = url_eachgame

            review_chunck = review_soup_s
            #======= review (how positive, n_votes, positive_percentage)
            # common
            regex = re.compile("Reviews:(.+)\(.*")
            regex2 = re.compile("of the(.*) user")
            regex3 = re.compile("-(.*)%")
            if len(review_chunck) == 1: # when only one review (then it's all_review)
                # recent_review
                df.loc[game, 'recent_review_positivity'] = 'NaN'
                df.loc[game, 'recent_reivew_nvotes'] = 'NaN'
                df.loc[game, 'recent_review_percentage'] = 'NaN'
                # all_review (content)
                all_content_raw = review_chunck[0].text

            else: # when both reviews exit (recent, all)
                # recent
                recent_content_raw = review_chunck[0].text
                recent_content = delete_trash(recent_content_raw)
                recent_split = recent_content.split(':')[1].split()
                recent_how_positive = regex.search(recent_content).group(1)
                recent_n_votes = regex2.search(recent_content).group(1)
                recent_positive_percentage = regex3.search(recent_content).group(1)
                df.loc[game, 'recent_review_positivity'] = recent_how_positive
                df.loc[game, 'recent_review_nvotes'] = recent_n_votes
                df.loc[game, 'recent_review_percentage'] = recent_positive_percentage
                # all review (content)
                all_content_raw = review_chunck[1].text

            # all_review (process & assign)
            all_content = delete_trash(all_content_raw)
            all_how_positive = regex.search(all_content).group(1)
            all_n_votes = regex2.search(all_content).group(1)
            all_positive_percentage = regex3.search(all_content).group(1)
            df.loc[game, 'all_review_positivity'] = all_how_positive
            df.loc[game, 'all_review_nvotes'] = all_n_votes
            df.loc[game, 'all_review_percentage'] = all_positive_percentage


            # features/developer/date
            micelles_soup = eachsoup.findAll('div', {'class':"block_content"})

            # ====== date
            date_chunck = micelles_soup[0].findAll('div', {'class':'date'})
            date = date_chunck[0].text
            df.loc[game, 'release_date'] = date
            # ====== developer
            tmp = micelles_soup[0].findAll('div', {'class':'summary column'})
            developer = tmp[2].find('a').text
            df.loc[game, 'developer'] = developer
            # ====== features
            feature_lists=[]
            feature_chunck = micelles_soup[0].findAll('a', {'class': 'app_tag'})
            for feature in range(len(feature_chunck)):
                feature_name = feature_chunck[feature].text
                feature_clean = delete_trash(feature_name)
                feature_lists.append(feature_clean)
        df.reindex(columns=column_names)
    return  df
    # recent_review, all_review, feature_game, release_date, developer_lists, weblink_worked, game_lists

def delete_trash(anystring):
    trash_list = ('\t', '\r', '\n')
    cleanstring1 = anystring.replace(trash_list[0], '')
    cleanstring2 = cleanstring1.replace(trash_list[1], '')
    cleanstring = cleanstring2.replace(trash_list[2], '')
    return cleanstring

if __name__ == "__main__":
    main(url, max_pages)
