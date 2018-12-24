import requests
import re
import os
import csv
import collections
from cltk.corpus.utils.importer import CorpusImporter
from cltk.stem.lemma import LemmaReplacer
from cltk.stem.latin.j_v import JVReplacer
from cltk.tokenize.word import WordTokenizer
from cltk.tag.pos import POSTag
my_latin_downloader = CorpusImporter('latin')
my_latin_downloader.import_corpus('latin_models_cltk')
# !!! ничто из cltk не будет работать если не скачать определенные архивы (в их тутуториале они указаны)
general_data = {}
stems = collections.Counter()


# скачивает работы одного автора и кладет их в его папку в 'Latin_Corpus'
def articles(author):
    address = author
    author = author[:-5]
    folder = 'Latin_Corpus'
    where = 'http://thelatinlibrary.com' + '/' + address
    plain_page = requests.get(where)
    work_chunk = re.compile('<div\sclass="work">(.*)</div>', re.DOTALL)
    work_chunks = re.findall(work_chunk, plain_page.text)
    files = []
    print(work_chunks)
    word_sum = 0
    for i in work_chunks:
        works = re.findall('href="(.*)">', i.lower())
        print(works)
        if len(works) > 6:
            for i in works:
                if word_sum <= 30000:
                    where = 'http://thelatinlibrary.com' + '/' + i
                    plain_text = requests.get(where)
                    work = re.compile(r'<p\sclass(.*)<div\sclass="footer">', re.DOTALL)
                    text = re.findall(work, plain_text.text)
                    words = ''.join(text)
                    words = words.split()
                    word_sum += len(words)
                    print(word_sum)
                    filename = '/' + str(i)
                    author_folder = works[0].split('/')[0]
                    author = author_folder
                    if not os.path.exists(folder + '/' + author_folder):
                        os.makedirs(folder + '/' + author_folder)
                    with open(folder + filename, 'w+', encoding='utf-8') as file:
                        file = file.write(''.join(text))
                        files.append(folder + filename)
                else:
                    break
            else:
                break

    print(files)
    return files, author


# ищет в тексте супплетивные и не оч формы сравнительной степени прилагательных
def forms_finder(files):
    word_sum = 0
    author_forms_used = {}
    compative_forms_file_num = 0
    suppletive_forms_file_num = 0
    while word_sum <= 100000:
        for i in files:
            with open(i, 'r', encoding='utf-8') as file:
                text = file.read()
                words = text.split()
            word_sum += len(words)
            print(word_sum)
        if word_sum >= 100000:
            for i in files:
                with open(i, 'r', encoding='utf-8') as file:
                    text = file.read()
                    text = text.lower()
                suppletive_forms = ['melior', 'melius', 'pejor', 'pejus', 'major', 'majus', 'minor', 'minus', 'plures', 'plura']
                comparative_forms = ('ior', 'ius', 'ioris', 'iori', 'iore', 'iores', 'iora', 'iorum', 'ioribus', 'iorem')
                words = text.split()
                suppletive_form_num = 0
                comparative_form_num = 0
                for word in words:
                    if word.endswith(comparative_forms):
                        if word in suppletive_forms:
                            suppletive_form_num += 1
                            stem = lemmatizer(word)
                            stems[stem[0]] += 1
                        else:
                            stem = lemmatizer(word)
                            stems[stem[0]] += 1
                            if stem != 'not_adjective':
                                comparative_form_num += 1
                            else:
                                continue
                    else:
                        if word in suppletive_forms:
                            suppletive_form_num += 1
                            stem = lemmatizer(word)
                            stems[stem[0]] += 1
                        else:
                            continue
                compative_forms_file_num += comparative_form_num
                suppletive_forms_file_num += suppletive_form_num
        else:
            print(word_sum)
        #этот параметр мы потом не использовали, но он считается (общее кол-во супплетивных и просто сравнительных форм)
    author_forms_used.update({'comparative_forms': compative_forms_file_num})
    author_forms_used.update({'suppletive_forms': suppletive_forms_file_num})
    print(author_forms_used)
    print(stems)
    return stems, word_sum


def lemmatizer(word):
    jv_replacer = JVReplacer()
    word = jv_replacer.replace(word)
    word_tokenizer = WordTokenizer('latin')
    tagger = POSTag('latin')
    word_tagged = tagger.tag_ngram_123_backoff(word)
    print(word_tagged)
    for i in word_tagged:
       # print(i[1])
        pos = str(i[1])
        if pos.startswith('A'):
            word = word_tokenizer.tokenize(word)
            lemmatizer = LemmaReplacer('latin')
            lemma = lemmatizer.lemmatize(word)
        else:
            lemma = 'not_adjective'
       # print(lemma)
    return lemma


def analyzer():
 # авторы такие потому что их страницы на thelatinlibrary.com нормально краулерятся
    author_tally = ['ammianus.html', 'apuleius.html', 'caes.html', 'cic.html', 'eutropius.html', 'frontinus.html',
                'gellius.html', 'sha.html', 'liv.html', 'lucan.html', 'lucretius.html', 'martial.html', 'nepos.html',
                 'ovid.html', 'plautus.html', 'quintilian.html', 'silius.html', 'statius.html', 'tac.html', 'verg.html']
    for author in author_tally:
        files, author = articles(author)
        stems, word_sum = forms_finder(files)
        del stems['n']
        data = author, word_sum, stems.most_common(10)
        csv_table_writer(data)
        print(author, 'done!')


def csv_table_creator():
    with open('to_lily_with_love.csv', mode='a+', encoding="utf-8") as csv_file:
        fieldnames = ['author', 'corpora_size', 'most_common_forms']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()


def csv_table_writer(data):
    author = data[0]
    corpora_size = data[1]
    most_common_forms = data[2]

    with open('to_lily_with_love.csv', mode='a+', encoding="utf-8") as csv_file:
        fieldnames = ['author', 'corpora_size', 'most_common_forms']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter='\t')
        writer.writerow({'author': author, 'corpora_size': corpora_size, 'most_common_forms': most_common_forms})


def main():
    csv_table_creator()
    analyzer()


if __name__ == '__main__':
    main()

