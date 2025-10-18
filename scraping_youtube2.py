from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
from collections import Counter
from itertools import tee, islice
import nltk
from nltk.corpus import stopwords

# === Setup NLTK stopwords ===
nltk.download('stopwords')
stop_words = set(stopwords.words('indonesian'))

# === 1. SCRAPING KOMENTAR YOUTUBE ===
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://www.youtube.com/watch?v=PMhfLy_buV8" 
driver.get(url)
time.sleep(5)

driver.execute_script("window.scrollTo(0, 600);")
time.sleep(3)

comments = []
target_comments = 1000
while len(comments) < target_comments:
    elements = driver.find_elements(By.XPATH, '//*[@id="content-text"]')
    for e in elements:
        text = e.text.strip()
        if text and text not in comments:
            comments.append(text)
            if len(comments) >= target_comments:
                break
    driver.execute_script("window.scrollBy(0, 2000);")
    time.sleep(3)

driver.quit()
print(f"Jumlah komentar yang diambil: {len(comments)}")

# === 2. REMOVE DUPLIKAT (jika masih ada) ===
comments = list(set(comments))
print(f"Setelah hapus duplikat: {len(comments)} komentar unik")

# === 3. NORMALISASI KATA ===
normalisasi = {
    "gk": "tidak", "ga": "tidak", "nggak": "tidak", "tdk": "tidak",
    "bgt": "banget", "aja": "saja", "yg": "yang", "udh": "sudah",
    "blm": "belum", "sm": "sama", "dr": "dari", "tp": "tapi",
    "kalo": "kalau", "krn": "karena", "makasih": "terima kasih"
}

def normalisasi_kata(text):
    for slang, baku in normalisasi.items():
        text = re.sub(rf"\b{slang}\b", baku, text)
    return text

# === 4. CLEANING DAN PREPROCESSING ===
def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)  # hapus link
    text = re.sub(r"[^a-zA-Z\s]", "", text)  # hapus tanda baca
    text = normalisasi_kata(text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in stop_words and len(t) > 2]
    return " ".join(tokens)

cleaned_comments = [clean_text(c) for c in comments]

# === 5. BIGRAM & TRIGRAM ===
def ngrams(text, n=2):
    words = text.split()
    return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]

all_bigrams = []
all_trigrams = []

for c in cleaned_comments:
    all_bigrams.extend(ngrams(c, 2))
    all_trigrams.extend(ngrams(c, 3))

bigram_counter = Counter(all_bigrams).most_common(10)
trigram_counter = Counter(all_trigrams).most_common(10)

print("\n🔥 Top 10 Bigram:")
for phrase, freq in bigram_counter:
    print(f"{phrase}: {freq}")

print("\n🔥 Top 10 Trigram:")
for phrase, freq in trigram_counter:
    print(f"{phrase}: {freq}")

# === 6. WORDCLOUD ===
all_text = " ".join(cleaned_comments)
wc = WordCloud(width=1000, height=500, background_color='white', colormap='plasma').generate(all_text)

plt.figure(figsize=(15,7))
plt.imshow(wc, interpolation='bilinear')
plt.axis('off')
plt.title("Word Cloud Komentar YouTube (Hasil Preprocessing)", fontsize=20)
plt.show()

wc.to_file("wordcloud_youtube_final.png")

# === 7. SIMPAN HASIL KE EXCEL ===
df = pd.DataFrame({
    "Komentar Asli": comments,
    "Komentar Bersih": cleaned_comments
})
df.to_excel("youtube_comments_preprocessed.xlsx", index=False, engine='openpyxl')

print("\n✅ Selesai! Semua tahap (scraping, preprocessing, normalisasi, bigram, trigram, wordcloud) berhasil dibuat.")
