# В ноутбуке или отдельном файле
import joblib

tfidf = joblib.load('data/model/transformers/tfidf.joblib')

# Смотрим что в словаре TF-IDF
vocab = tfidf.vocabulary_
print("Всего слов:", len(vocab))

# Есть ли жанры?
test_words = ['action', 'romance', 'horror', 'comedy', 'drama',
              'science_fiction', 'thriller']
for w in test_words:
    print(f"  '{w}': {'✓ есть' if w in vocab else '✗ НЕТ'}")