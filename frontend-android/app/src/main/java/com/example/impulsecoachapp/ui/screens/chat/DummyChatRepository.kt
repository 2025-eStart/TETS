package com.example.impulsecoachapp.ui.screens.chat

////////////////// API 연동 버전 //////////////////
/*
// [전체 흐름]
// Android App (Compose) ➡️ Retrofit ➡️ FastAPI 서버 ➡️ LLM API (ChatGPT/Gemini)
// 나중에는 Hilt나 Koin 같은 의존성 주입 라이브러리를 사용해서
// ChatViewModel에 DummyChatRepository 대신 ActualChatRepository를 주입하게 됩니다.

package com.example.impulsecoachapp.data.ActualChat // 패키지 경로는 예시입니다.

import com.example.impulsecoachapp.model.chat.ChatMessage
import com.example.impulsecoachapp.domain.repository.ChatRepository

// Retrofit Service 인터페이스가 필요합니다.
// interface ChatApiService {
//     @POST("chat")
//     suspend fun postMessage(@Body messageRequest: MessageRequest): MessageResponse
// }

class ActualChatRepository(
    // private val apiService: ChatApiService // Retrofit 인터페이스
) : ChatRepository {

    override suspend fun getNextMessage(userInput: String): ChatMessage {
        return try {
            // 1. FastAPI 서버로 사용자 입력을 전송
            // val response = apiService.postMessage(MessageRequest(text = userInput))

            // 2. 서버로부터 받은 응답을 ChatMessage.GuideMessage 로 변환
            // ChatMessage.GuideMessage(response.text)

            // 아래는 임시 코드입니다.
            ChatMessage.GuideMessage("'$userInput'에 대한 API 응답입니다.")

        } catch (e: Exception) {
            // 3. 네트워크 에러 등 예외 처리
            ChatMessage.GuideMessage("죄송해요, 지금은 답변을 드릴 수 없어요. (에러: ${e.message})")
        }
    }
}
*
* */
