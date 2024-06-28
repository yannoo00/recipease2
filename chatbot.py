from flask import Blueprint, request, jsonify
from transformers import BertTokenizer
from recommender import load_model_and_embeddings, recommend_recipe, generate_response, price, youtube_crawl, search_nutrient

chatbot_bp = Blueprint('chatbot', __name__)
loaded_model, loaded_embeddings = load_model_and_embeddings('model_embeddings_all.pkl')
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

@chatbot_bp.route('/chatbot', methods=['POST'])
def process_user_input():
    try:
        user_input = request.json['message']
        print(f"User input: {user_input}")  # 로그 추가
        recommendation_response = recommend_recipe(user_input, loaded_model, loaded_embeddings, tokenizer)

        if recommendation_response is None:
            return jsonify({
                'chatbot_response': "결과를 찾지 못했습니다. 더 자세한 입력을 부탁드립니다.",
                'price_results': None,
                'youtube_result': None,
                'nutrient_data': None
            })

        chatbot_response = generate_response(PERSONA, user_input, recommendation_response)
        price_results = price(chatbot_response)
        youtube_result = youtube_crawl(chatbot_response)
        nutrient_data = search_nutrient(chatbot_response)

        response_data = {
            'recommendation_response': recommendation_response,
            'chatbot_response': chatbot_response,
            'price_results': price_results,
            'youtube_result': youtube_result,
            'nutrient_data': nutrient_data
        }
        print(f"Response data: {response_data}")  # 로그 추가

        return jsonify(response_data)
    except Exception as e:
        error_message = f"오류 발생: {str(e)}"
        print(error_message)  # 로그 추가
        return jsonify({'error': error_message}), 500