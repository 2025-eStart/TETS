package com.example.impulsecoachapp.data.repository

import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.domain.model.ChatTurn
import com.example.impulsecoachapp.domain.repository.ChatRepository
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

////////////////// API 연동 없는 버전 //////////////////
@Singleton // [추가] Hilt가 관리하도록 싱글톤 설정
class DummyChatRepository @Inject constructor() : ChatRepository {

    // [수정] 인터페이스의 'sendChatMessage' 함수를 구현(override)합니다.
    override suspend fun sendChatMessage(
        text: String,
        endSession: Boolean
    ): Result<ChatTurn> {

        // API 호출 흉내
        delay(1000)

        // 세션 종료 요청(endSession=true)을 먼저 처리합니다.
        if (endSession) {
            val endMessage = ChatMessage.GuideMessage("상담이 종료되었습니다. 수고하셨습니다.")
            val chatTurn = ChatTurn(
                assistantMessage = endMessage,
                isSessionEnded = true,
                homework = null
            )
            return Result.success(chatTurn)
        }

        // [수정] 기존 'getNextMessage'의 로직을 그대로 사용합니다. (userInput -> text)
        val botMessage = when (text) {
            "네 있었어요" -> ChatMessage.GuideMessage("무슨 소비였는지 말해줄 수 있어?")
            "잘 모르겠어요" -> ChatMessage.GuideMessage("최근에 충동적이었다고 느낀 순간이 있을까?")
            else -> ChatMessage.GuideMessage("그렇구나, '$text'에 대해 좀 더 자세히 이야기해줄래?")
        }

        // [수정] 반환 타입을 Result<ChatTurn>에 맞춥니다.
        val chatTurn = ChatTurn(
            assistantMessage = botMessage,
            isSessionEnded = false, // 기본값은 false
            homework = null
        )
        return Result.success(chatTurn)
    }

}
