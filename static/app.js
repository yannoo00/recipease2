document.addEventListener('DOMContentLoaded', function() {
    
    displayInitialMessage();
    
    document.getElementById('sendButton').addEventListener('click', sendMessage);
    document.getElementById('userInput').addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
    });

    function displayInitialMessage() {
        var messagesDiv = document.getElementById('messages');
        var initialMessage = "안녕하세요! 레시피 추천 챗봇 레시피즈입니다.<br>재료/상황/취향 등을 입력해주세요.";
        messagesDiv.innerHTML += '<div class="bot-message">' + initialMessage + '</div>';
    }

    function sendMessage() {
        var userInput = document.getElementById('userInput').value;
        if (userInput.trim() !== '') {
            var messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML += '<div class="user-message">' + userInput + '</div>';
            document.getElementById('userInput').value = '';
        
            // 답변 생성 중 메시지 추가
            var loadingMessage = '<div class="bot-message" id="loading-message">답변을 생성중이에요...</div>';
            messagesDiv.innerHTML += loadingMessage;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            fetch('/chatbot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userInput })
            })
            .then(response => response.json())
            .then(data => {
                
                // 답변 생성 중 메시지 제거
                var loadingMessageElement = document.getElementById('loading-message');
                if (loadingMessageElement) {
                    loadingMessageElement.remove();
                }

                // if (data.chatbot_response) {
                //     messagesDiv.innerHTML += '<div class="bot-message"><strong>챗봇 응답:</strong><br>' + data.chatbot_response.replace(/\n/g, '<br>') + '</div>';
                // } else {
                //     messagesDiv.innerHTML += '<div class="bot-message">결과를 찾지 못했습니다. 더 자세한 입력을 부탁드립니다.</div>';
                // }   
                if (data.chatbot_response) {
                    messagesDiv.innerHTML += '<div class="bot-message">제가 추천하는 레시피는 다음과 같습니다!<br>';
                } else {
                    messagesDiv.innerHTML += '<div class="bot-message">결과를 찾지 못했습니다. 더 자세한 입력을 부탁드립니다.</div>';
                }                   

                if (data.chatbot_response) {
                    messagesDiv.innerHTML += '<div class="bot-message"><strong>추천 레시피:</strong><br>' + data.chatbot_response.replace(/\n/g, '<br>') + '</div>';
                }
                if (data.price_results) {
                    var priceHtml = '<div class="bot-message"><strong>재료 가격 정보:</strong><br>';
                    data.price_results.forEach(function(result) {
                        priceHtml += '<p><a href="' + result.url + '" target="_blank">' + result.product_name + ' - ' + result.product_price + '</a></p>';
                    });
                    priceHtml += '</div>';
                    messagesDiv.innerHTML += priceHtml;
                }
                if (data.youtube_result) {
                    var videoId = getYouTubeVideoId(data.youtube_result['Video URL']);
                    var youtubeHtml = '<div class="bot-message"><strong>관련 유튜브 영상:</strong><br><br>';
                    youtubeHtml += '<iframe width="560" height="315" src="https://www.youtube.com/embed/' + videoId + '" frameborder="0" allowfullscreen></iframe>';
                    youtubeHtml += '<p>' + data.youtube_result['Title'] + '</p>';
                    youtubeHtml += '<p>조회수: ' + data.youtube_result['Views'] + ' | 업로드 시간: ' + data.youtube_result['Period'] + '</p>';
                    youtubeHtml += '</div>';
                    messagesDiv.innerHTML += youtubeHtml;
                }
                if (data.nutrient_data) {
                    var nutrientHtml = '<div class="bot-message"><strong>영양정보(100g당/1일영양섭취기준):</strong><br>';
                    nutrientHtml += '<p>음식 이름: ' + data.nutrient_data.dish_name + '</p>';
                    nutrientHtml += '<ul>';
                    data.nutrient_data.nutrients.forEach(function(nutrient, index) {
                        var value = nutrient.value_g;
                        var unit = nutrient.unit;
                        if (index === 0) {
                            unit = 'kcal';
                        }
                        else{
                            unit = 'g';
                        }
                        nutrientHtml += '<li>' + nutrient.name + ': ' + value + unit + ' (' + nutrient.percentage + '%)</li>';
                    });
                    nutrientHtml += '</ul></div>';
                    messagesDiv.innerHTML += nutrientHtml;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // 답변 생성 중 메시지 제거
                var loadingMessageElement = document.getElementById('loading-message');
                if (loadingMessageElement) {
                    loadingMessageElement.remove();
                }
                messagesDiv.innerHTML += '<div class="bot-message">결과를 찾지 못했습니다. 더 자세히 입력해주세요.</div>';
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            });
        }
    }
    
    function getYouTubeVideoId(url) {
        var videoId = '';
        var match = url.match(/[?&]v=([^&#]*)/);
        if (match) {
            videoId = match[1];
        }
        return videoId;
    }
})