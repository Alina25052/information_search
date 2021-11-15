from elasticsearch import Elasticsearch
from beautifultable import BeautifulTable
from wiki_ru_wordnet import WikiWordnet
import sys
import os
import json

class Search_by_index: #главный класс для индекса
    def __init__(self):
        self.es = Elasticsearch()
        self.ww = WikiWordnet()

    # функция создания индекса
    def create_index(self):
        indexItem = 'flowers' #задаем имя
        bodyItem = {        #и тело индексирования
            'settings': {
                'number_of_shards': 1, #кол-во первичных шардов
                'number_of_replicas': 0, #кол-во реплик для первичных шардов
                'analysis': { #настроим анализатор
                    'filter': {
                        'ru_stop': {
                                'type': 'stop',
                                'stopwords': '_russian_'
                            }
                        # 'ru_stemmer': {
                        #         'type': 'stemmer',
                        #         'language': 'russian'
                        #     }
                        },
                    'analyzer': {
                        'default': {
                                'tokenizer': 'standart',
                                'filter': ['snowball', 'lowercase', 'worlddelimiter', 'ru_stop']
                            }
                        }
                    }
                }
            }
            #получаем доступ к IndicesClient и создаем индекс с параметрами
        self.es.indices.create(index = indexItem, body = bodyItem, ignore = 400)
    
    def delete_index(self): #функция удаления (происходит после выхода)
        for key in self.es.indices.get_alias().keys():
            self.es.indices.delete(index = key)

    def add_index(self):
        if (len(sys.argv) > 2 or len(sys.argv) < 2):
            path = input('Введите путь к json файлу:\n')
        with open(path, 'r',encoding = 'utf-8') as file_stream:
            data = json.loads(file_stream.read())
            i = 0
            for item in data:
                self.es.index(index = 'flowers', id = i, body = item)
                i += 1

    def add_synonyms(self, query):
        tmp_list = list()
        result_tokens = self.es.indices.analyze(index='flowers', body={
            'analyzer': 'default',
            'text': [query]
        })
        for token in result_tokens['tokens']:
            tmp_list.append(token['token'])
            syn_sets = self.ww.get_synsets(token['token'])
            if syn_sets:
                for synonym in syn_sets[0].get_words():
                    word = synonym.lemma()
                    if tmp_list.count(word) == 0:
                        tmp_list.append(word)
        return ' '.join(tmp_list)

    def find_response(self, option, request):
        fields_list = [['title'], ['body'], ['title', 'body']]
        field = fields_list[int(option) - 1]
        bodyItem = {
            'query': { #настроим запрос
                'bool': {
                    'should': [
                        {
                            'multi_match': {
                                'query': request,
                                'analyzer': 'default',
                                'fields': field
                            }
                        },
                    ],
                }
            }
        }
        return self.es.search(index = 'flowers', body = bodyItem)

if __name__ == '__main__':
    index = Search_by_index() #создадим объект класса
    index.delete_index() #удалим предыдущий индекс
    index.create_index() #создадим индекс
    index.add_index() #добавим данные к нему
    n = 0
    while (1):
        n = input('Введите n, чтобы:\n' +
              '1 - провести поиск по названию цветов\n' +
              '2 - провести поиск по ключевым словам цветка\n' + 
              '3 - провести поиск по названию и ключевым словам цветка\n' +
              '4 - выйти\n')
        if n in ['1', '2', '3']:
            request = index.add_synonyms(input('Введите запрос: '))
            print(f'\nПоиск синонимов: {request}')
            res = index.find_response(n, request)
            res_len = len(res['hits']['hits'])
            if res_len > 0:
                table = BeautifulTable()
                for i in range(res_len):
                    number = i + 1
                    name = res['hits']['hits'][i]['_source']['title']
                    score = res['hits']['hits'][i]['_score']
                    #price = res['hits']['hits'][i]['_source']['price']
                    URL = res['hits']['hits'][i]['_source']['url']
                    table.rows.append([number, name, score,URL])
                table.columns.header = ['Номер', 'Название цветов', 'Рейтинг','URL']
                print(table)
        else:
            if (n != '4'):
                print('Введены некорректные данные...')
            break
