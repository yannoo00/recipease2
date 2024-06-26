document.addEventListener('DOMContentLoaded', () => {
    const messagesContainer = document.getElementById('messages');
    const userInput = document.getElementById('userInput');
    const recommendationsContainer = document.getElementById('recommendations');

    function addMessage(user, text, element) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', user);
        
        if (element) {
            messageElement.appendChild(element);
        } else {
            messageElement.textContent = text;
        }
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function sendMessage() {
        const userMessage = userInput.value.trim();
        if (userMessage) {
            addMessage('user', userMessage);
            userInput.value = '';
            const recommendationData = await fetchRecommendations(userMessage);
            displayRecommendations(recommendationData);
        }
    }

    async function fetchRecommendations(message) {
        const response = await fetch('/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });
        const data = await response.json();
        return {
            chatbot_response: data.chatbot_response,
            nutrient_info: data.nutrient_info,
            youtube_info: data.youtube_info,
            price_info: data.price_info
        };
    }
    
    function displayRecommendations(recommendationData) {
        const { chatbot_response, nutrient_info, youtube_info, price_info } = recommendationData;
    
        if (chatbot_response) {
            addMessage('bot', chatbot_response);
    
        // 영양 정보 표시
        let nutrientMessage = '영양 정보:\n';
        if (nutrient_info && nutrient_info.nutrients && nutrient_info.nutrients.length > 0) {
            nutrient_info.nutrients.forEach(nutrient => {
                nutrientMessage += `- ${nutrient.name}: ${nutrient.value_g}g (${nutrient.percentage}%)\n`;
            });
        } else if (typeof nutrient_info === 'string') {
            nutrientMessage += nutrient_info;
        } else {
            nutrientMessage += '영양 정보가 없습니다.';
        }
        addMessage('bot', nutrientMessage);

        // 가격 정보 표시
        let priceMessage = '가격 정보:\n';
        if (price_info && price_info.length > 0) {
            price_info.forEach(item => {
                priceMessage += `- ${item.ingredient}: ${item.product_name} - ${item.product_price}\n`;
            });
        } else {
            priceMessage += '가격 정보가 없습니다.';
        }
        addMessage('bot', priceMessage);
    
            // 유튜브 정보 표시
            let youtubeMessage = '유튜브 정보:\n';
            if (youtube_info && youtube_info.Title) {
                youtubeMessage += `제목: ${youtube_info.Title}\n`;
                youtubeMessage += `조회수: ${youtube_info.Views}\n`;
                youtubeMessage += `업로드 날짜: ${youtube_info.Period}\n`;
                
                const thumbnailUrl = youtube_info['Image URL'];
                const thumbnailElement = document.createElement('img');
                thumbnailElement.src = thumbnailUrl;
                thumbnailElement.alt = '유튜브 썸네일';
                thumbnailElement.style.maxWidth = '100%';
                
                addMessage('bot', youtubeMessage);
                addMessage('bot', '', thumbnailElement);
            } else if (typeof youtube_info === 'string') {
                youtubeMessage += youtube_info;
                addMessage('bot', youtubeMessage);
            } else {
                youtubeMessage += '유튜브 정보가 없습니다.';
                addMessage('bot', youtubeMessage);
            }
        } else {
            addMessage('bot', '추천 결과가 없습니다.');
        }
    }

    window.sendMessage = sendMessage;

});
