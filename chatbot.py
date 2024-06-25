from flask import Blueprint, request, jsonify
from transformers import BertTokenizer
from recommender import load_model_and_embeddings, recommend_recipe, generate_response, price, youtube_crawl, search_nutrient

chatbot_bp = Blueprint('chatbot', __name__)
loaded_model, loaded_embeddings = load_model_and_embeddings('model_embeddings.pkl')
tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')

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

@chatbot_bp.route('/recommend', methods=['POST'])
def process_user_input():
    try:
        user_input = request.json['message']
        recommendation_response = recommend_recipe(user_input, loaded_model, loaded_embeddings, tokenizer)
        chatbot_response = generate_response(PERSONA, user_input, recommendation_response)
        
        nutrient_info = search_nutrient(chatbot_response)
        youtube_info = youtube_crawl(chatbot_response)
        price_info = price(chatbot_response)

        return jsonify({
            'chatbot_response': chatbot_response,
            'nutrient_info': nutrient_info,
            'youtube_info': youtube_info,
            'price_info': price_info
        })
    except Exception as e:
        error_message = f"오류 발생: {str(e)}"
        return jsonify({'error': error_message}), 500