


document.addEventListener('DOMContentLoaded', () => {
    const messagesContainer = document.getElementById('messages');
    const userInput = document.getElementById('userInput');
    const recommendationsContainer = document.getElementById('recommendations');

    function addMessage(user, text) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', user);
        messageElement.textContent = text;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function sendMessage() {
        const userMessage = userInput.value.trim();
        if (userMessage) {
            addMessage('user', userMessage);
            userInput.value = '';
            const chatbot_response = await fetchRecommendations(userMessage);
            addMessage('bot', chatbot_response);
            displayRecommendations(chatbot_response);
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
        
        recommendationsContainer.innerHTML = '';
        if (chatbot_response) {
            const recipeElement = document.createElement('div');
            recipeElement.textContent = chatbot_response;
            recommendationsContainer.appendChild(recipeElement);
    
            // 영양 정보 표시
            const nutrientElement = document.createElement('div');
            nutrientElement.textContent = '영양 정보:';
            if (nutrient_info && nutrient_info.nutrients && nutrient_info.nutrients.length > 0) {
                const nutrientList = document.createElement('ul');
                nutrient_info.nutrients.forEach(nutrient => {
                    const listItem = document.createElement('li');
                    listItem.textContent = `${nutrient.name} - ${nutrient.value_g}g (${nutrient.percentage}%)`;
                    nutrientList.appendChild(listItem);
                });
                nutrientElement.appendChild(nutrientList);
            } else {
                nutrientElement.textContent += ' 영양 정보가 없습니다.';
            }
            recommendationsContainer.appendChild(nutrientElement);
    
            // 가격 정보 표시
            const priceElement = document.createElement('div');
            priceElement.textContent = '가격 정보:';
            if (price_info && price_info.length > 0) {
                const priceList = document.createElement('ul');
                price_info.forEach(item => {
                    const listItem = document.createElement('li');
                    listItem.textContent = `${item.ingredient} - ${item.product_name} - ${item.product_price}`;
                    priceList.appendChild(listItem);
                });
                priceElement.appendChild(priceList);
            } else {
                priceElement.textContent += ' 가격 정보가 없습니다.';
            }
            recommendationsContainer.appendChild(priceElement);
    
            // 유튜브 정보 표시
            const youtubeElement = document.createElement('div');
            youtubeElement.textContent = '유튜브 정보:';
            if (youtube_info && youtube_info.Title) {
                const youtubeInfo = document.createElement('div');
                youtubeInfo.innerHTML = `
                    <p>제목: ${youtube_info.Title}</p>
                    <p>조회수: ${youtube_info.Views}</p>
                    <p>업로드 날짜: ${youtube_info.Period}</p>
                    <img src="${youtube_info['Image URL']}" alt="유튜브 썸네일">
                `;
                youtubeElement.appendChild(youtubeInfo);
            } else {
                youtubeElement.textContent += ' 유튜브 정보가 없습니다.';
            }
            recommendationsContainer.appendChild(youtubeElement);
        } else {
            recommendationsContainer.textContent = '추천 결과가 없습니다.';
        }
    }


    window.sendMessage = sendMessage; // 이 부분을 이벤트 리스너 내부로 이동

});