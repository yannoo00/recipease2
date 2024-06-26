from typing import List
import requests
import re
import time
import urllib.parse
from bs4 import BeautifulSoup
import pickle
import pandas as pd
import torch
from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity
import openai
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from config import OPENAI_API_KEY
import boto3
import io


# Set OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

# Parameters
MODEL_NAME = "gpt-4"
TEMPERATURE = 0

PERSONA = """
다음 절차를 따라 사용자의 질문에 답변.

첫째, 사용자가 제공한 조건에 따라 데이터에서 해당 레시피들을 찾아서 해당 내용을 구체적으로 답변.
둘째, 만약 제공한 조건에 따른 데이터가 많아도 하나만 출력.
셋째, 데이터에 적합한 내용이 없으면 대답하지 않음.
넷째, 각 레시피를 다음과 같이 출력.

  요리 이름:
  종류:
  필요한 재료:
  난이도:
  요리 시간:
"""

def load_model_and_embeddings(file_path):
    """Load BERT model and embeddings from a local file."""
    with open(file_path, 'rb') as file:
        model, embeddings = pickle.load(file)
    print(f"Model and embeddings loaded from local file: {file_path}")
    return model, embeddings

def get_bert_embeddings(text_list, tokenizer, model):
    """Generate BERT embeddings for a list of texts."""
    inputs = tokenizer(text_list, return_tensors='pt', padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).numpy()

def recommend_recipe(user_input, model, data_embeddings, tokenizer, file_path='Recipe_Info.txt'):
    """Recommend recipes based on user input using BERT embeddings."""
    data = pd.read_csv(file_path, delimiter='\t', header=None, names=["combined_features"])
    user_embedding = get_bert_embeddings([user_input], tokenizer, model)
    user_embedding = user_embedding.reshape(1, -1)  # 차원 조정 추가

    print(f"data_embeddings shape: {data_embeddings.shape}")  # 차원 확인 코드 추가
    if len(data_embeddings.shape) == 3:
        data_embeddings = data_embeddings.reshape(data_embeddings.shape[0], -1)  # 차원 조정 코드 추가
        print(f"Reshaped data_embeddings shape: {data_embeddings.shape}")  # 차원 조정 후 확인 코드 추가

    sim_scores = cosine_similarity(user_embedding, data_embeddings).flatten()
    sim_indices = sim_scores.argsort()[-5:][::-1]
    recommendations = [(data.iloc[i]['combined_features'], sim_scores[i]) for i in sim_indices]

    print("Selected Top 5 Recipes:")
    for i, (recipe, score) in enumerate(recommendations, start=1):
        print(f"Recipe {i}:")
        print(f"Similarity Score: {score}")
        print(recipe)
        print("-" * 20)    
    
    response = ""
    for recipe, score in recommendations:
        response += f"Similarity Score: {score}\n"
        response += f"{recipe}\n"
        response += "-" * 20 + "\n"

    if recommendations[0][1] <= 0.5:
        return None
    return response

def generate_response(persona, user_input, recommendation_response):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": recommendation_response}],
        temperature=0
    )
    message = response.choices[0].message.content
    return message

# Function to search for ingredient on Coupang
def search_ingredient_on_coupang(ingredient):

    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("prefs", {"prfile.managed_default_content_setting.images": 2})

    driver = webdriver.Chrome(options=options)
    main_url = f"https://www.kurly.com/search?sword={ingredient}"

    try:
        # 검색 결과 페이지 요청
        driver.get(main_url)
        time.sleep(5)
        # 첫 번째 상품 링크 가져오기

        element=driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/main/div[2]/div[2]/div[2]/a[1]')
        sub_url=element.get_attribute('href')

        # 상품명
        product=driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/main/div[2]/div[2]/div[2]/a[1]/div[3]/span[2]').text

        # 가격
        price=driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/main/div[2]/div[2]/div[2]/a[1]/div[3]/div[1]/div/span/span[1]').text

        # 결과를 딕셔너리로 반환
        return {
            "ingredient": ingredient,
            "url": sub_url,
            "product_name": product,
            "product_price": str(price)+' 원'
        }

    except Exception as e:
        return {
            "ingredient": ingredient,
            "error": f"오류 발생"
        }

    finally:
        driver.quit()

def price(recommendations):
    def extract_ingredients(text):
      match = re.search(r"필요한 재료:\s*([^\n]+)", text)
      if match:
          ingredients = match.group(1).strip().split(", ")
          return ingredients
      else:
          return ["필요한 재료를 찾을 수 없습니다."]

    if recommendations:
        detailed_text = recommendations

        # Extract ingredients from the detailed text
        ingredients_list = extract_ingredients(detailed_text)
        # Search for each ingredient in Coupang
        results = [search_ingredient_on_coupang(ingredient.split()[0]) for ingredient in ingredients_list[:3]]

    return results

def extract_recipe_title(response):
    # "요리 이름:"으로 시작하는 줄을 찾기
    for line in response.split('\n'):
        if line.startswith("요리 이름: "):
            # "요리 이름:" 뒤의 단어를 추출
            dish_name = line.split(": ")[1]
            print(dish_name)
            return dish_name

def youtube_crawl(recommendations):
  # Extract the title of the top recommended recipe
  top_recommendation = recommendations
  recipe_title = extract_recipe_title(top_recommendation)
  SEARCH_KEYWORD = str(recipe_title) + ' 레시피'

  # 브라우저 꺼짐 방지 및 불필요한 에러 메시지 없애기
  chrome_options = Options()
  chrome_options.add_experimental_option("detach", True)
  chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
  chrome_options.add_argument("--headless")
  chrome_options.add_argument("--no-sandbox")
  chrome_options.add_argument("--disable-dev-shm-usage")

  # 불필요한 에러 메시지 없애기
  browser = webdriver.Chrome(options=chrome_options)

  # 스크래핑 할 URL 세팅
  URL = "https://www.youtube.com/results?search_query=" + SEARCH_KEYWORD
  # 크롬 드라이버를 통해 지정한 URL의 웹 페이지 오픈
  browser.get(URL)
  # 웹 페이지 로딩 대기
  time.sleep(3)

  # XPath 설정
  img_xpath = '//*[@id="thumbnail"]/yt-image/img'
  title_xpath = '//*[@id="video-title"]'
  viewcnt_xpath = '//*[@id="metadata-line"]/span[1]'
  period_xpath = '//*[@id="metadata-line"]/span[2]'
#  url_xpath = '//*[@id="video-title"]'

  # 요소 찾기
  image = browser.find_element(By.XPATH, img_xpath)
  img_url = image.get_attribute('src')

  title = browser.find_element(By.XPATH, title_xpath)
  view = browser.find_element(By.XPATH, viewcnt_xpath)
  period = browser.find_element(By.XPATH, period_xpath)
  video_element = browser.find_element(By.CSS_SELECTOR, "a#video-title")
  video_url = video_element.get_attribute('href')

  title_list = []
  view_list = []
  periods_list = []
  urls_list = []

  title_list.append(title.text)
  view_list.append(view.text)
  periods_list.append(period.text)
  urls_list.append(video_url)

  result = {
    'Title': title.text,
    'Views': view.text,
    'Period': period.text,
    'Image URL': img_url,
    'Video URL': video_url
    }

  # 브라우저 종료
  browser.quit()

  return result

def setup_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(options=chrome_options)

def search_nutrient(input_value):
    def extract_nutrient_data(driver):
        nutrient_data = []
        for i in range(1, 6):
            nutrient_xpath = f'//*[@id="content"]/div[5]/div[1]/div/div[{i}]'

            try:
                nutrient_element = driver.find_element(By.XPATH, nutrient_xpath)
                nutrient_text = nutrient_element.text
                parts = nutrient_text.split()

                nutrient_name = parts[0]
                g_value = parts[1]
                percentage = parts[-1]

                if len(parts) > 2 and parts[1] == parts[2]:
                    g_value = parts[1]

                g_value_numeric = ''.join(filter(lambda x: x.isdigit() or x == '.', g_value))
                percentage_numeric = ''.join(filter(lambda x: x.isdigit() or x == '.', percentage))

                nutrient_info = {
                    'name': nutrient_name,
                    'value_g': g_value_numeric,
                    'percentage': percentage_numeric
                }

                nutrient_data.append(nutrient_info)
            except Exception as e:
                print(f"영양성분 추출 오류")

        return nutrient_data

    driver = setup_driver()
    input_value = extract_recipe_title(input_value)

    try:
        driver.get("https://various.foodsafetykorea.go.kr/nutrient/")
        search_box = driver.find_element(By.ID, "searchText")
        search_box.send_keys(input_value)

        search_button = driver.find_element(By.CLASS_NAME, "btn")
        search_button.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="simpleDataBody"]/tr[1]/td[3]/a/em')))

        dish_name_element = driver.find_element(By.XPATH, '//*[@id="simpleDataBody"]/tr[1]/td[3]/a/em')
        dish_name = dish_name_element.text

        first_result = driver.find_element(By.CSS_SELECTOR, '#simpleDataBody > tr:nth-child(1) > td:nth-child(3) > a:nth-child(1)')
        first_result.click()

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div[5]/div[1]/div/div[1]')))

        nutrient_data = extract_nutrient_data(driver)

        return {'dish_name': dish_name, 'nutrients': nutrient_data}

    except Exception as e:
        return f"요청하는 데이터를 찾지 못하거나 오류가 발생함."

    finally:
        driver.quit()

def main():
    """Main function to run the recipe recommendation system."""
    # Load the BERT model and embeddings
    file_path = 'model_embeddings_all.pkl'
    loaded_model, loaded_embeddings = load_model_and_embeddings(file_path)

    # Initialize BERT tokenizer
    tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')

    print("Chatbot is now running. Type 'exit' to quit.")
    while True:
        user_input = input("User: ")
        if user_input.lower() == 'exit':
            break
        recommendation_response = recommend_recipe(user_input, loaded_model, loaded_embeddings, tokenizer)
        if recommendation_response is None:
            print(None)
            continue
        chatbot_response = generate_response(PERSONA, user_input, recommendation_response)
        print(recommendation_response)
        print(chatbot_response)
        print(price(chatbot_response), sep='\n')
        print(youtube_crawl(chatbot_response))
        print(search_nutrient(chatbot_response))

if __name__ == "__main__":
    main()
