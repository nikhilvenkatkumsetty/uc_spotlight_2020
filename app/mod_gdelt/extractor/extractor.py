from .schema import v2_header, v1_header, article_columns, cameo, dtype_map

from multiprocessing import Pool, cpu_count
from datetime import datetime, timedelta
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from newspaper import Article
from itertools import chain
from functools import wraps
import pandas as pd
import numpy as np
import traceback
import requests
import tempfile
import zipfile
import shutil
import pytz
import time
import os
import re

import warnings
warnings.filterwarnings("ignore")


class Extractor(object):

    def __init__(self):

        self.scratch = os.path.split(os.path.realpath(__file__))[0]

        self.v2_urls = self.get_v2_urls()
        self.v1_urls = self.get_v1_urls()

        self.articles = False

    @staticmethod
    def get_v2_urls():

        return {
            'last_update': 'http://data.gdeltproject.org/gdeltv2/lastupdate.txt'
        }

    @staticmethod
    def get_v1_urls():

        return {
            'events': 'http://data.gdeltproject.org/events'
        }

    @staticmethod
    def text_filter(text):

        return re.sub('[^a-zA-Z0-9 \n]', '', text)

    @staticmethod
    def batch_it(l, n):

        for i in range(0, len(l), n):
            yield l[i:i + n]

    @staticmethod
    def extract_csv(csv_url, temp_dir):

        response = requests.get(csv_url, stream=True)

        zip_name = csv_url.split('/')[-1]
        zip_path = os.path.join(temp_dir, zip_name)

        with open(zip_path, 'wb') as file: file.write(response.content)
        with zipfile.ZipFile(zip_path, 'r') as the_zip: the_zip.extractall(temp_dir)

        txt_name = zip_name.strip('export.CSV.zip')
        txt_name += '.txt'
        txt_path = os.path.join(temp_dir, txt_name)

        os.rename(zip_path.strip('.zip'), txt_path)

        return txt_path

    @staticmethod
    def batch_process_articles(article_list):

        processed_data = []

        for event_article in article_list:

            try:
                # Parse GDELT Source
                article = Article(event_article[1])
                article.download()
                article.parse()
                article.nlp()

                # Unpack Article Properties & Replace Special Characters
                title     = article.title.replace("'", '')
                site      = urlparse(article.source_url).netloc
                summary   = '{} . . . '.format(article.summary.replace("'", '')[:500])
                summary   = re.sub('<.*?>', '', summary)
                keywords  = '; '.join(sorted([re.sub('[^a-zA-Z0-9 \n]', '', key) for key in article.keywords]))
                meta_keys = '; '.join(sorted([re.sub('[^a-zA-Z0-9 \n]', '', key) for key in article.meta_keywords]))

                processed_data.append([event_article[0], title, site, summary, keywords, meta_keys])

            except:
                processed_data.append([event_article[0], None, None, None, None, None])

        return processed_data

    def temp_handler(func):

        @wraps(func)
        def wrap(*args, **kwargs):

            temp_dir = tempfile.mkdtemp()

            args = list(args)
            args.insert(1, temp_dir)

            try:
                func(*args, **kwargs)
            except:
                print(traceback.format_exc())
            finally:
                shutil.rmtree(temp_dir)

        return wrap

    def article_enrichment(self, article_list):

        batches = list(self.batch_it(article_list, int(len(article_list) / cpu_count() - 1)))

        # Create Pool & Run Records
        pool = Pool(processes=cpu_count() - 1)
        data = pool.map(self.batch_process_articles, batches)
        pool.close()
        pool.join()

        return list(chain(*data))

    def process_df(self, df, extracted_date):

        # Discard Anything Without a Coordinate
        df.dropna(subset=['ActionGeo_Long', 'ActionGeo_Lat'], inplace=True)

        # Keep First Unique URL
        df.drop_duplicates('SOURCEURL', inplace=True)

        # Get Most of the Things - We Need to Use our Schema to be Smarter About This
        df.fillna('0', inplace=True)

        # Insert Column to Identify When it was Extracted
        df['extracted_date'] = pd.to_datetime(extracted_date).replace(tzinfo=pytz.UTC)

        # Avoid Python Integer Overflow Errors
        df['GLOBALEVENTID'] = df['GLOBALEVENTID'].astype('str')
        df['EventRootCode'] = df['EventRootCode'].astype('str')
        df['DATEADDED']     = df['DATEADDED'].astype('str')

        # Map Root Code to Cameo Definition
        df['CATEGORY'] = df['EventRootCode'].apply(lambda x: cameo.get(x, 'Other'))

        # Create & Append Article Information
        if self.articles:
            a_dt = self.article_enrichment(df[['GLOBALEVENTID', 'SOURCEURL']].values.tolist())
            a_df = pd.DataFrame(a_dt, columns=article_columns)
            df = df.merge(a_df, on='GLOBALEVENTID')

        # Build Geometry
        df = df.spatial.from_xy(df, 'ActionGeo_Long', 'ActionGeo_Lat')

        return df

    def fetch_last_v2_url(self):

        response = requests.get(self.v2_urls.get('last_update'))
        last_url = [r for r in response.text.split('\n')[0].split(' ') if 'export' in r][0]

        return last_url

    def fetch_last_v1_url(self):

        response = requests.get(f"{self.v1_urls.get('events')}/index.html")
        the_soup = BeautifulSoup(response.content[:2000], features='lxml')
        last_csv = the_soup.find_all('a')[3]['href']
        last_url = f"{self.v1_urls.get('events')}/{last_csv}"

        return last_url

    def collect_v1_csv(self, temp_dir):

        last_url = self.fetch_last_v1_url()

        csv_file = self.extract_csv(last_url, temp_dir)

        # CSV File Name Will be Converted to Date & Stored in "Extracted_Date" Column
        csv_name = os.path.basename(csv_file).split('.')[0]

        return csv_file, csv_name

    def collect_v2_csv(self, temp_dir):

        last_url = self.fetch_last_v2_url()

        csv_file = self.extract_csv(last_url, temp_dir)

        # CSV File Name Will be Converted to Date & Stored in "Extracted_Date" Column
        csv_name = os.path.basename(csv_file).split('.')[0]

        return csv_file, csv_name

    def get_v2_sdf(self, csv_file, csv_name):

        try:
            df = pd.read_csv(csv_file, sep='\t', names=v2_header, dtype=dtype_map)

            return self.process_df(df, csv_name)

        except Exception as gen_exc:
            print(f'Error Building SDF: {gen_exc}')

    def get_v1_sdf(self, csv_file, csv_name):

        try:
            # Convert csv into a pandas dataframe. See schema.py for columns processed from GDELT 2.0
            df = pd.read_csv(csv_file, sep='\t', names=v1_header, dtype=dtype_map)

            return self.process_df(df, csv_name)

        except Exception as gen_exc:
            print(f'Error Building SDF: {gen_exc}')

    def get_v2(self):

        temp_dir = tempfile.mkdtemp()

        try:
            # Collect & Unpack Latest 15 Minute CSV Dump
            csv_file, csv_name = self.collect_v2_csv(temp_dir)

            # Convert Current 15 Minute GDELT Data to Spatial Data Frame
            sdf = self.get_v2_sdf(csv_file, csv_name)

            return sdf

        finally:
            shutil.rmtree(temp_dir)

